from django.template import Library

import backtosql


register = Library()


def is_column(value):
    if isinstance(value, backtosql.TemplateColumn):
        return True
    return False


@register.filter
def only_column(value, prefix=None):
    if is_column(value):
        return value.only_column(prefix=prefix)

    # else its a collection
    return ", ".join([x.only_column(prefix=prefix) for x in value])


@register.filter
def only_alias(value, prefix=None):
    if is_column(value):
        return value.only_alias(prefix=prefix)

    # else its a collection
    return ", ".join([x.only_alias(prefix=prefix) for x in value])


@register.filter
def column_as_alias(value, prefix=None):
    if is_column(value):
        return value.column_as_alias(prefix=prefix)

    # else its a collection
    return ", ".join([x.column_as_alias(prefix=prefix) for x in value])


@register.filter
def generate(q, prefix=None):
    if not q:
        return '1=1'

    return q.generate(prefix=prefix)


@register.filter
def lspace(value):
    return " " + str(value).strip() if value else value


@register.filter
def as_kw(value):
    return " AS " + str(value).strip() if value else value


@register.filter
def indices(value):
    return ", ".join([str(x) for x in range(1, len(value) + 1)])
