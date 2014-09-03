import datetime

from decimal import Decimal


class Node:
    def __init__(self, parent=None, **kw):
        self.parent = parent


class CompositeNode(Node):
    def __init__(self, children=None, **kw):
        super().__init__(**kw)
        if children is None:
            self.children = []
        else:
            self.children = children
            self.reparent_children()

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def append(self, child):
        child.parent = self
        self.children.append(child)

    def remove(self, child):
        self.children.remove(child)

    def reparent_children(self):
        for child in self.children:
            child.parent = self


class Journal(CompositeNode):
    def __init__(self, name='', **kw):
        super().__init__(**kw)
        self.name = name


class Status:
    def __init__(self, status=None, **kw):
        self.status = {
            'pending': False,
            'cleared': False,
        }
        if status is not None:
            self.status.update(status)


class Transaction(CompositeNode, Status):
    def __init__(self, date, description, auxdate=None, code=None,
                 note=None, **kw):
        super().__init__(**kw)
        self.date = create_date(date)
        self.auxdate = create_date(auxdate)
        self.code = code
        self.description = description
        self.note = note


class Posting(Node, Status):
    def __init__(self, account, amount, note=None, **kw):
        super().__init__(**kw)
        self.account = account
        self.amount = amount
        self.note = note


class Account(Node):
    def __init__(self, name, flags=None, **kw):
        super().__init__(**kw)
        self.flags = {
            'virtual': False,
            'balanced': False,
            'deferred': False,
        }
        if flags is not None:
            self.flags.update(flags)
        self.name = name


def D(str_ord=None):
    if str_ord is None:
        return Decimal()
    elif isinstance(str_ord, str):
        return Decimal(str_ord)
    elif isinstance(str_ord, Decimal):
        return str_ord
    elif isinstance(str_ord, (float, int)):
        return Decimal(str_ord)


class Amount(Node):
    def __init__(self, amount, symbol=None, **kw):
        super().__init__(**kw)
        if amount is not None:
            self.amount = D(amount)
        else:
            self.amount = amount
        self.symbol = symbol


def create_date(date_tuple):
    if date_tuple is None:
        return None
    year, month, day = date_tuple
    if year is None:
        return PartialDate(int(month), int(day))
    else:
        return datetime.date(int(year), int(month), int(day))


class PartialDate:
    # February is set to 29 days for leap years.
    _days_in_month = [None, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def __init__(self, month, day):
        self.replace(month, day)

    def replace(self, month, day):
        if 1 <= month <= 12:
            self.month = month
        else:
            raise ValueError('month must be in 1..12', month)
        dim = self._days_in_month[month]
        if 1 <= day <= dim:
            self.day = day
        else:
            raise ValueError('day must be in 1..{}'.format(dim), day)
        return self

    def isoformat(self):
        return '{:02d}-{:02d}'.format(self.month, self.day)

    def __str__(self):
        return self.isoformat()


class Note(Node):
    def __init__(self, text, **kw):
        super().__init__(**kw)
        self.text = text
        self.tags = {}


class Comment(Node):
    def __init__(self, text, **kw):
        super().__init__(**kw)
        self.text = text


class EmptyLine(Node):
    def __init__(self, **kw):
        super().__init__(**kw)
