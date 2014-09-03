import logging

from ply.yacc import NullLogger

from ledgerbeans.lexer import LedgerLexer, LexError
from ledgerbeans.parser import LedgerParser
from ledgerbeans.printer import printer


logger = logging.getLogger(__name__)


def command_ast(args):
    lexer = LedgerLexer(args.file)

    if args.debug:
        parser = LedgerParser(lexer, errorlog=logger, debug=logger)
    else:
        parser = LedgerParser(lexer, errorlog=NullLogger())

    try:
        ast = parser.parse()
    except LexError as e:
        logger.error('{}:{}:{}:{}'.format(e.state.file.name,
                                          e.state.lineno,
                                          e.state.lexpos + 1,
                                          e.message))
    else:
        # TODO write to args.output.
        for line in printer(ast):
            args.output.write(line + '\n')
