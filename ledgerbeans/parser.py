import logging
import ply.yacc as yacc

from ledgerbeans import ast


logger = logging.getLogger(__name__)


class LedgerParser:
    def p_journal1(self, p):
        '''journal : items EOF'''
        p[0] = ast.Journal(name=p[2], children=p[1])

    def p_items1(self, p):
        '''items : items item'''
        p[1].append(p[2])
        p[0] = p[1]

    def p_items2(self, p):
        '''items : empty'''
        p[0] = []

    def p_item1(self, p):
        '''item : xact_directive
                | comment_directive'''
        p[0] = p[1]

    def p_item2(self, p):
        '''item : EMPTYLINE'''
        p[0] = ast.EmptyLine()

    def p_comment_directive(self, p):
        '''comment_directive : COMMENT TEXT'''
        p[0] = ast.Comment(p[2])

    def p_xact_directive(self, p):
        '''xact_directive : DATE auxdate_opt status_opt code_opt DESCRIPTION note_opt xact_postings'''
        p[0] = ast.Transaction(date=p[1],
                               auxdate=p[2],
                               status=p[3],
                               code=p[4],
                               description=p[5],
                               note=p[6],
                               children=p[7])

    def p_auxdate_opt(self, p):
        '''auxdate_opt : AUXDATE
                       | empty'''
        p[0] = p[1]

    def p_status_opt1(self, p):
        '''status_opt : CLEARED'''
        p[0] = {'cleared': True, }

    def p_status_opt2(self, p):
        '''status_opt : PENDING'''
        p[0] = {'pending': True, }

    def p_status_opt3(self, p):
        '''status_opt : empty'''
        p[0] = {}

    def p_code_opt(self, p):
        '''code_opt : CODE
                    | empty'''
        p[0] = p[1]

    def p_note_opt(self, p):
        '''note_opt : note
                    | empty'''
        p[0] = p[1]

    def p_note(self, p):
        '''note : NOTE TEXT'''
        p[0] = ast.Note(p[2])

    def p_xact_postings1(self, p):
        '''xact_postings : xact_postings xact_posting'''
        p[1].append(p[2])
        p[0] = p[1]

    def p_xact_postings2(self, p):
        '''xact_postings : empty'''
        p[0] = []

    def p_xact_posting1(self, p):
        '''xact_posting : INDENT status_opt account amount_opt note_opt'''
        p[0] = ast.Posting(status=p[2],
                           account=p[3],
                           amount=p[4],
                           note=p[5])

    def p_xact_posting2(self, p):
        '''xact_posting : INDENT note'''
        p[0] = p[2]

    def p_account1(self, p):
        '''account : ACCOUNT'''
        p[0] = ast.Account(name=p[1])

    def p_account2(self, p):
        '''account : VIRTACC'''
        p[0] = ast.Account(name=p[1], flags={'virtual': True})

    def p_account3(self, p):
        '''account : BALVIRTACC'''
        p[0] = ast.Account(name=p[1], flags={'virtual': True,
                                             'balanced': True})

    def p_account4(self, p):
        '''account : DEFERREDACC'''
        p[0] = ast.Account(name=p[1], flags={'deferred': True})

    def p_amount_opt1(self, p):
        '''amount_opt : AMOUNT symbol_opt'''
        print(p[2])
        p[0] = ast.Amount(amount=p[1], symbol=p[2])

    def p_amount_opt2(self, p):
        '''amount_opt : empty'''
        p[0] = p[1]

    def p_symbol_opt(self, p):
        '''symbol_opt : SYMBOL
                      | empty'''
        p[0] = p[1]

    def p_empty(self, p):
        '''empty :'''
        pass

    def p_error(self, p):
        # TODO Clean up error reporting.
        if p is None:
            logger.error('Unexpected EOF?')
        else:
            logger.error('{}:{}:Syntax error'.format(p.lineno, p.lexpos))
            raise SyntaxError

    def __init__(self, lexer, **kw):
        self.lexer = lexer
        self.tokens = lexer.tokens
        self.parser = yacc.yacc(module=self, **kw)

    def parse(self):
        return self.parser.parse(lexer=self.lexer)
