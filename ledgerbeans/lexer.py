from collections import deque

import logging


logger = logging.getLogger(__name__)


class LexToken:
    def __init__(self, type, value=None, lineno=None, lexpos=None):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos

    def __str__(self):
        return 'LexToken({0.type!s}, {0.value!r}, ' \
               '{0.lineno:d}, {0.lexpos:d})'.format(self)

    def __repr__(self):
        return str(self)


class LexError(Exception):
    def __init__(self, message, state=None):
        self.message = message
        self.state = state


class LexState:
    def __init__(self, f):
        self.file = f
        self.line = None
        self.lineno = 0
        self.linelen = 0
        self.lexpos = 0
        self.tokens = deque()
        self.directive = None
        self.null_amount_posting = False

    def __iter__(self):
        return self

    def __next__(self):
        line = next(self.file)
        line = line.rstrip()
        self.lineno += 1
        self.linelen = len(line)
        self.lexpos = 0
        self.line = line
        return line

    def __str__(self):
        return 'LexState({0.lineno:r},{0.lexpos:r}/{0.linelen:r})' \
               '={0.line}'.format(self)

    def get_token(self):
        return self.tokens.popleft()

    def add_token(self, token):
        self.tokens.append(token)

    def add_tokens(self, tokens):
        self.tokens.extend(tokens)

    def next_word_pos(self, pos=None, skip=True):
        if pos is None:
            pos = self.lexpos
        text = self.line[pos:]
        ws_found = False
        for i, char in enumerate(text):
            if ws_found:
                if not char.isspace():
                        return pos + i
            else:
                if char.isspace():
                    ws_found = True
                elif not skip:
                    return pos + i
        return -1

    def next_hard_word_pos(self, pos=None, skip=True):
        if pos is None:
            pos = self.lexpos
        text = self.line[pos:]
        ws_found = False
        ws_count = 0
        tab_count = 0
        for i, char in enumerate(text):
            if ws_found:
                if not char.isspace():
                    if tab_count >= 1 or ws_count >= 2:
                        return pos + i
                    else:
                        ws_found = False
                        ws_count = 0
                        tab_count = 0
                elif char == '\t':
                    tab_count += 1
                else:
                    ws_count += 1
            else:
                if char == '\t':
                    ws_found = True
                    tab_count += 1
                elif char.isspace():
                    ws_found = True
                    ws_count += 1
                elif not skip:
                    return pos + i
        return -1

    def next_whitespace_pos(self, pos=None):
        if pos is None:
            pos = self.lexpos
        text = self.line[pos:]
        for i, char in enumerate(text):
            if char.isspace():
                return pos + i
        return -1

    def next_char_pos(self, char, pos=None, hard_sep=False):
        if pos is None:
            pos = self.lexpos
        char_pos = self.line.find(char, pos)
        if hard_sep:
            if char_pos < 1:
                return -1
            elif char_pos == 1 and self.line[0] == '\t':
                return char_pos
            elif char_pos > 1 and (
                    self.line[char_pos-1].isspace() and
                    self.line[char_pos-2].isspace()):
                return char_pos
            else:
                return -1
        else:
            return char_pos

    def next_word(self, skip=True, hard_sep=False):
        if hard_sep:
            next_pos = self.next_hard_word_pos(skip=skip)
        else:
            next_pos = self.next_word_pos(skip=skip)
        if next_pos == -1:
            if self.linelen > 0:
                self.lexpos = self.linelen - 1
            return None
        self.lexpos = next_pos
        ws_pos = self.next_whitespace_pos()
        if ws_pos > -1 and ws_pos > next_pos:
            return self.line[next_pos:ws_pos]
        else:
            return self.line[next_pos:]


class LedgerLexer:
    directive_dict = {
        ' ': 'indent',
        '\t': 'indent',
        ';': 'comment_directive',
        '#': 'comment_directive',
        '*': 'comment_directive',
        '|': 'comment_directive',
        '-': 'option_directive',
        '0': 'xact_directive',
        '1': 'xact_directive',
        '2': 'xact_directive',
        '3': 'xact_directive',
        '4': 'xact_directive',
        '5': 'xact_directive',
        '6': 'xact_directive',
        '7': 'xact_directive',
        '8': 'xact_directive',
        '9': 'xact_directive',
    }

    flag_dict = {
        '*': 'CLEARED',
        '!': 'PENDING',
    }

    account_dict = {
        '(': ('VIRTACC', ')', 'virtual'),
        '[': ('BALVIRTACC', ']', 'balanced virtual'),
        '<': ('DEFERREDACC', '>', 'deferred'),
    }

    expression_dict = {
        'assert': 'ASSERT',
        'check': 'CHECK',
        'expr': 'EXPR'
    }

    marker_list = ['.', ',']

    sign_list = ['-', '+']

    symbol_invalid_list = ['.', ',', ';', ':', '?', '!',
                           '-', '+', '*', '/', '^', '&', '|', '=',
                           '<', '>', '[', ']', '(', ')', '{', '}',
                           '@']

    tokens = [
        'EMPTYLINE', 'EOF',
        'COMMENT',
        'OPTION', 'ARGUMENT',
        'DATE', 'AUXDATE', 'CODE',
        'DESCRIPTION', 'NOTE', 'TEXT',
        'INDENT', 'ACCOUNT',
        'VALEXPR', 'AMOUNT', 'SYMBOL',
    ] + list(flag_dict.values()) + \
        [a for a, b, c in account_dict.values()] + \
        list(expression_dict.values())

    def __init__(self, f):
        self.stack = []
        self.state = LexState(f)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    @property
    def lineno(self):
        return self.state.lineno

    @property
    def lexpos(self):
        return self.state.lexpos

    def token(self):
        try:
            return self.state.get_token()
        except IndexError:
            try:
                line = next(self.state)
            except StopIteration:
                return self.eof()
            try:
                char = line[0]
            except IndexError:
                self.emptyline()
                return self.token()
            if char in self.directive_dict:
                getattr(self, self.directive_dict[char])()
                return self.token()
            return None
        except AttributeError:
            # Reached EOF of last state in stack
            return None

    def next(self):
        token = self.token()
        if token is None:
            raise StopIteration
        return token

    def emptyline(self):
        self.state.directive = 'emptyline'
        self.state.add_token(LexToken('EMPTYLINE', None,
                                      self.state.lineno, self.state.lexpos))

    def eof(self):
        filename = self.state.file.name
        lineno = self.state.lineno
        lexpos = self.state.linelen
        try:
            self.state = self.stack.pop()
        except IndexError:
            self.state = None
        return LexToken('EOF', filename, lineno, lexpos)

    def indent(self):
        if self.state.directive == 'xact':
            self.indent_xact()

    def indent_xact(self):
        def next_word_and_check(skip=True):
            word = self.state.next_word(skip)
            if word is None or not len(word):
                raise LexError('Missing account in posting', self.state)
            return word

        self.state.add_token(LexToken('INDENT', None,
                                      self.state.lineno,
                                      self.state.lexpos))

        word = next_word_and_check()
        comment_tokens = []
        if word[0] == ';':
            note_pos = self.state.lexpos
        else:
            note_pos = self.state.next_char_pos(';', hard_sep=True)
        if note_pos != -1:
            save_pos = self.state.lexpos
            self.state.lexpos = note_pos
            comment_tokens = self.tokenize_xact_note()
            if save_pos == note_pos:
                # Line with only a comment.
                self.state.add_tokens(comment_tokens)
                return
            # Strip comment from line and continue lexing.
            self.state.line = self.state.line[:note_pos]
            self.state.line = self.state.line.rstrip()
            self.state.lexpos = save_pos
            self.state.linelen = len(self.state.line)
            word = next_word_and_check(skip=False)

        if word in self.expression_dict:
            tokens = self.tokenize_xact_expression(word)
            self.state.add_tokens(tokens)
            self.state.add_tokens(comment_tokens)
            return
        elif word[0] in self.flag_dict:
            token = self.flag_dict[word[0]]
            self.state.add_token(LexToken(token, word[0],
                                          self.state.lineno,
                                          self.state.lexpos))
            word = next_word_and_check()

        account = ''
        skip = True
        if word[0] in self.account_dict:
            token, close_char, name = self.account_dict[word[0]]
            pos = self.state.next_char_pos(close_char)
            ws_pos = self.state.next_hard_word_pos()
            if pos == -1:
                raise LexError("Missing closing '{}' "
                               "in {} posting".format(close_char, name),
                               self.state)
            elif -1 < ws_pos < pos:
                raise LexError('No hard separator allowed in account name',
                               self.state)
            account = self.state.line[self.state.lexpos+1:pos]
        else:
            token = 'ACCOUNT'
            pos = self.state.next_hard_word_pos()
            if pos == -1:
                account = self.state.line[self.state.lexpos:]
            else:
                account = self.state.line[self.state.lexpos:pos]
                # Next word is already found at next character
                skip = False
        account = account.strip()
        if not len(account):
            raise LexError('Missing account in virtual posting',
                           self.state)
        self.state.add_token(LexToken(token, account,
                                      self.state.lineno,
                                      self.state.lexpos))

        # This only advances lexpos while lexing a virtual posting.
        self.state.lexpos = pos
        word = self.state.next_word(hard_sep=True, skip=skip)
        if word is not None:
            if word[0] == '(':
                tokens = self.tokenize_amount_expression()
                self.state.add_tokens(tokens)
            else:
                tokens = self.tokenize_amount(word)
                self.state.add_tokens(tokens)

            word = self.state.next_word(skip=False)
            if word is not None:
                print('----')
                print(word)

        self.state.add_tokens(comment_tokens)

    def comment_directive(self):
        self.state.directive = 'comment'
        char = self.state.line[self.state.lexpos]
        self.state.add_token(LexToken('COMMENT', char,
                                      self.state.lineno,
                                      self.state.lexpos))
        self.state.lexpos += 1
        pos = self.state.next_word_pos(skip=False)
        if pos != -1:
            text = self.state.line[pos:]
            self.state.lexpos = pos
            self.state.add_token(LexToken('TEXT', text,
                                          self.state.lineno,
                                          pos))

    def option_directive(self):
        self.state.directive = 'option'
        try:
            if self.state.line[1] == '-':
                # double --
                start = 2
            else:
                # single -
                start = 1
        except IndexError:
            raise LexError('Missing option name', self.state)

        pos = self.state.line.find('=', start)
        if pos == start:
            # --=
            self.state.lexpos = pos
            raise LexError('Missing option name', self.state)
        elif pos > -1:
            option = self.state.line[start:pos]
            pos += 1
            argument = self.state.line[pos:]
        else:
            # No assignment after option.
            pos = self.state.next_word_pos(pos=start)
            if pos > -1:
                option = self.state.line[start:pos-1]
                argument = self.state.line[pos:]
            else:
                # Option without argument.
                option = self.state.line[start:]
                argument = None

        self.state.add_token(LexToken('OPTION', option,
                                      self.state.lineno, start))
        if argument:
            self.state.add_token(LexToken('ARGUMENT', argument,
                                          self.state.lineno, pos))

    def xact_directive(self):
        def next_word_and_check():
            word = self.state.next_word()
            if word is None or not len(word):
                raise LexError('Missing payee or description in transaction',
                               self.state)
            return word

        self.state.directive = 'xact'
        date_string = self.state.next_word(skip=False)
        if date_string is None:
            raise LexError('Invalid date', self.state)
        tokens = self.tokenize_xact_date(date_string)
        self.state.add_tokens(tokens)

        word = next_word_and_check()
        if word[0] in self.flag_dict:
            token = self.flag_dict[word[0]]
            self.state.add_token(LexToken(token, word[0],
                                          self.state.lineno,
                                          self.state.lexpos))
            word = next_word_and_check()

        tokens = self.tokenize_xact_code()
        if len(tokens):
            self.state.add_tokens(tokens)
            word = next_word_and_check()

        note_pos = self.state.next_char_pos(';', hard_sep=True)
        if note_pos == -1:
            description = self.state.line[self.state.lexpos:]
        else:
            description = self.state.line[self.state.lexpos:note_pos]
        description = description.strip()
        self.state.add_token(LexToken('DESCRIPTION', description,
                                      self.state.lineno,
                                      self.state.lexpos))
        if note_pos > -1:
            self.state.lexpos = note_pos
            tokens = self.tokenize_xact_note()
            self.state.add_tokens(tokens)

    def tokenize_xact_date(self, text):
        tokens = []
        date_string = text
        aux_date_string = None
        aux_pos = text.find('=')
        if aux_pos > -1:
            aux_date_string = text[aux_pos+1:]
            if not len(aux_date_string):
                self.state.lexpos += aux_pos
                raise LexError('Missing auxiliary date', self.state)
            date_string = text[:aux_pos]
        date = self.scan_date(date_string)
        tokens.append(LexToken('DATE', date,
                               self.state.lineno, self.state.lexpos))
        if aux_date_string:
            self.state.lexpos += aux_pos + 1
            date = self.scan_date(aux_date_string)
            tokens.append(LexToken('AUXDATE', date,
                                   self.state.lineno, self.state.lexpos))
        return tokens

    def tokenize_xact_code(self):
        tokens = []
        if self.state.line[self.state.lexpos] == '(':
            pos = self.state.next_char_pos(')')
            if pos == -1:
                raise LexError("Missing closing ')' after code in transaction",
                               self.state)
            code = self.state.line[self.state.lexpos+1:pos]
            self.state.lexpos += 1
            code = code.strip()
            if not len(code):
                raise LexError('Missing code in transaction', self.state)
            tokens.append(LexToken('CODE', code,
                                   self.state.lineno, self.state.lexpos))
        return tokens

    def tokenize_xact_note(self):
        tokens = []
        char = self.state.line[self.state.lexpos]
        if char == ';':
            tokens.append(LexToken('NOTE', char,
                                   self.state.lineno, self.state.lexpos))
            self.state.lexpos += 1
            pos = self.state.next_word_pos(skip=False)
            if pos > -1:
                text = self.state.line[pos:]
                self.state.lexpos = pos
                tokens.append(LexToken('TEXT', text,
                                       self.state.lineno, self.state.lexpos))
        return tokens

    def tokenize_xact_expression(self, text):
        tokens = []
        token = self.expression_dict[text]
        tokens.append(LexToken(token, text,
                               self.state.lineno, self.state.lexpos))
        pos = self.state.next_word_pos()
        if pos == -1:
            raise LexError('Missing value expression', self.state)
        value_expr = self.state.line[pos:]
        value_expr = value_expr.strip()
        self.state.lexpos = pos
        tokens.append(LexToken('VALEXPR', value_expr,
                               self.state.lineno, self.state.lexpos))
        return tokens

    def scan_amount_number(self, char):
        number = ''
        while char.isdecimal() or char in self.marker_list:
            if char in self.marker_list and number[-1] in self.marker_list:
                raise LexError("Unexpected character '{}'".format(char),
                               self.state)
            number += char
            self.state.lexpos += 1
            try:
                char = self.state.line[self.state.lexpos]
            except IndexError:
                break
        return number

    def scan_amount_symbol(self, char):
        symbol = ''
        while True:
            if char.isdecimal() or char.isspace() or \
               char in self.symbol_invalid_list:
                break
            else:
                symbol += char
                self.state.lexpos += 1
                try:
                    char = self.state.line[self.state.lexpos]
                except IndexError:
                    break
        return symbol

    def scan_amount_quoted_symbol(self):
        start = self.state.lexpos
        end = self.state.next_char_pos('"', pos=start+1)
        if end == -1:
            raise LexError('Missing closing quote character', self.state)
        self.state.lexpos = end + 1
        return self.state.line[start:end+1]

    def scan_date(self, text):
        for c in ['-', '.']:
            text = text.replace(c, '/')
        parts = text.split('/')
        l = len(parts)
        if l == 3:
            year = parts[0]
            month = parts[1]
            day = parts[2]
        elif l == 2:
            year = None
            month = parts[0]
            day = parts[1]
        else:
            raise LexError('Invalid date', self.state)
        return (year, month, day)

    def tokenize_amount(self, word=None):
        def check_unexpected_character(check, char):
            if check:
                raise LexError("Unexpected character '{}'".format(char),
                               self.state)

        tokens = []
        sign = ''
        number = ''
        symbol = ''

        symbol_prefix = False
        symbol_space = False
        number_grouping = False

        sign_done = False
        number_done = False
        symbol_done = False

        char = self.state.line[self.state.lexpos]
        while True:
            if char in self.sign_list:
                check_unexpected_character(sign_done, char)
                sign = char
                self.state.lexpos += 1
                sign_done = True
            elif char.isdecimal():
                check_unexpected_character(number_done, char)
                number_pos = self.state.lexpos
                number = self.scan_amount_number(char)
                number_done = True
                sign_done = True
                if symbol_done:
                    symbol_prefix = True
            elif char == '"':
                check_unexpected_character(symbol_done, char)
                symbol_pos = self.state.lexpos
                symbol = self.scan_amount_quoted_symbol()
                symbol_done = True
            elif char == ' ':
                try:
                    peek_char = self.state.line[self.state.lexpos+1]
                except IndexError:
                    # Reached end of line, no need to continue.
                    break
                if peek_char.isspace():
                    # Double whitespace not allowed inside amount.
                    break
                if number_done and symbol_done:
                    # Done with amount, no need to continue.
                    break
                if (number_done and not symbol_done) or \
                   (symbol_done and not number_done):
                    symbol_space = True
                self.state.lexpos += 1
            else:
                check_unexpected_character(symbol_done, char)
                symbol_pos = self.state.lexpos
                symbol = self.scan_amount_symbol(char)
                symbol_done = True

            if number_done and symbol_done:
                # Break when amount consists of both a number and a symbol.
                break
            else:
                try:
                    char = self.state.line[self.state.lexpos]
                except IndexError:
                    # Break when end of line.
                    break

        # Any characters left without whitespace are invalid.
        try:
            char = self.state.line[self.state.lexpos]
        except IndexError:
            pass
        else:
            check_unexpected_character(char.isspace(), char)

        if not number_done:
            raise LexError('No quantity specified for amount', self.state)
        if sign_done:
            number = sign + number
        tokens.append(LexToken('AMOUNT', number,
                               self.state.lineno, number_pos))

        # TODO determine number grouping.

        if symbol_done:
            symbol_flags = ''
            if symbol_prefix:
                symbol_flags += 'P'
            if symbol_space:
                symbol_flags += 'S'
            if number_grouping:
                symbol_flags += 'T'
            tokens.append(LexToken('SYMBOL', (symbol, symbol_flags),
                                   self.state.lineno, symbol_pos))
        return tokens

    def tokenize_amount_expression(self):
        tokens = []
        # TODO
        return tokens
