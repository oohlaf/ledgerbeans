import logging

from ledgerbeans.lexer import LedgerLexer, LexError


logger = logging.getLogger(__name__)


def command_lex(args):
    lexer = LedgerLexer(args.file)
    try:
        for token in lexer:
            args.output.write(str(token) + '\n')
    except LexError as e:
        logger.error('{}:{}:{}:{}'.format(e.state.file.name,
                                          e.state.lineno,
                                          e.state.lexpos + 1,
                                          e.message))
