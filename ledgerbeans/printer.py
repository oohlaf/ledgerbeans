import reg

from ledgerbeans import ast


def args_printer_helper(obj, attrs=[]):
    args = []
    for attr in attrs:
        value = getattr(obj, attr)
        if value is not None:
            args.append('{}={}'.format(attr, value))
    return args


@reg.generic
def printer(obj):
    raise NotImplementedError


def journal_printer(journal):
    yield 'journal(name={0.name})'.format(journal)
    for item in journal:
        for line in printer(item):
            yield ' ' + line
    return


def transaction_printer(xact):
    args = []
    args.extend(args_printer_helper(xact, ['date', 'auxdate', 'code',
                                           'description']))
    if xact.note is not None:
        for line in printer(xact.note):
            args.append(line)
    yield 'transaction({})'.format(', '.join(args))
    for item in xact:
        for line in printer(item):
            yield ' ' + line
    return


def post_printer(post):
    args = []
    if post.account is not None:
        for line in printer(post.account):
            args.append(line)
    if post.amount is not None:
        for line in printer(post.amount):
            args.append(line)
    if post.note is not None:
        for line in printer(post.note):
            args.append(line)
    yield 'post({})'.format(', '.join(args))
    return


def account_printer(account):
    yield 'account(name={0.name})'.format(account)
    return


def amount_printer(amount):
    yield 'amount(amount={0.amount}, symbol={0.symbol})'.format(amount)
    return


def note_printer(note):
    yield 'note(text={0.text})'.format(note)
    return


def comment_printer(comment):
    yield 'comment(text={0.text})'.format(comment)
    return


def empty_line_printer(item):
    yield 'emptyline()'
    return


def register(registry=None):
    if registry is None:
        registry = reg.Registry()
    registry.register(printer, [ast.Journal], journal_printer)
    registry.register(printer, [ast.Transaction], transaction_printer)
    registry.register(printer, [ast.Posting], post_printer)
    registry.register(printer, [ast.Account], account_printer)
    registry.register(printer, [ast.Amount], amount_printer)
    registry.register(printer, [ast.Note], note_printer)
    registry.register(printer, [ast.Comment], comment_printer)
    registry.register(printer, [ast.EmptyLine], empty_line_printer)
