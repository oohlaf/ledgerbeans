import argparse
import logging
import reg
import sys

from ledgerbeans import version
from ledgerbeans.command.lex import command_lex
from ledgerbeans.command.ast import command_ast


log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}
logger = logging.getLogger()


def configure_logging(args):
    logger.setLevel(log_levels[args.log_level])
    console_log = logging.StreamHandler(stream=sys.stderr)
    logger.addHandler(console_log)


def register(registry=None):
    if registry is None:
        registry = reg.Registry()
    from ledgerbeans.printer import register as register_printer
    register_printer(registry)
    reg.implicit.initialize(registry)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    register()

    main_arg = argparse.ArgumentParser(add_help=False)
    main_arg.add_argument('--version', action='version',
                          version='%(prog)s {}'.format(version),
                          help="print version information and exit")
    main_arg.add_argument('--debug', default=False,
                          action='store_true',
                          help="enable debug mode")
    main_arg.add_argument('--log-level', metavar='LEVEL',
                          choices=log_levels.keys(), default='warning',
                          help="set logging to LEVEL, where LEVEL is "
                          "one of %(choices)s; default is %(default)s")
    main_arg.add_argument('-f', '--file', metavar='FILE',
                          type=argparse.FileType('r'),
                          default=sys.stdin,
                          help="read FILE as a ledger file")
    main_arg.add_argument('-o', '--output', metavar='FILE',
                          type=argparse.FileType('w'),
                          default=sys.stdout,
                          help="redirect output to FILE")

    # file_arg = argparse.ArgumentParser(add_help=False)

    parser = argparse.ArgumentParser(parents=[main_arg],
                                     description="Double-entry "
                                     "accounting tool",
                                     epilog="See '%(prog)s help <command>' "
                                     "to read about a specific command and "
                                     "its arguments.")
    subparsers = parser.add_subparsers(title='available commands',
                                       dest='command',
                                       metavar='<command>')

    lex_parser = subparsers.add_parser('lex', parents=[main_arg],
                                       description="Show tokens after lexing "
                                       "and exit",
                                       help="show tokens after lexing "
                                       "and exit")
    lex_parser.set_defaults(cmd_func=command_lex)

    ast_parser = subparsers.add_parser('ast', parents=[main_arg],
                                       description="Show abstract syntax tree "
                                       "after parsing and exit",
                                       help="show AST after parsing "
                                       "and exit")
    ast_parser.set_defaults(cmd_func=command_ast)

    args = parser.parse_args(argv)
    configure_logging(args)
    print(args.command)
    args.cmd_func(args)


if __name__ == '__main__':
    sys.exit(main())
