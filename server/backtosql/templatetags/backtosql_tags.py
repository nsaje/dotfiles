from django.template import Library

import backtosql


register = Library()


def is_column(value):
    if isinstance(value, backtosql.TemplateColumn):
        return True
    return False

def _generate(func_name, columns, prefix):
    if getattr(columns, func_name, None) and callable(getattr(columns, func_name, None)):
        return getattr(columns, func_name)(prefix=prefix)
    return ", ".join([getattr(x, func_name)(prefix=prefix) for x in columns])


@register.filter
def only_column(value, prefix=None):
    if is_column(value):
        value.only_column(prefix=prefix)

    # else its a collection
    return ", ".join([x.only_column(prefix=prefix) for x in value])


@register.filter
def only_alias(value, prefix=None):
    if is_column(value):
        value.only_alias(prefix=prefix)

    # else its a collection
    return ", ".join([x.only_alias(prefix=prefix) for x in value])



@register.filter
def column_as_alias(value, prefix=None):
    if is_column(value):
        value.column_as_alias(prefix=prefix)

    # else its a collection
    return ", ".join([x.column_as_alias(prefix=prefix) for x in value])


@register.filter
def generate(q, prefix=None):
    q.generate(prefix=prefix)


@register.filter
def lspace(value):
    return " " + str(value).strip() if value else value


@register.filter
def as_kw(value):
    return " AS " + str(value).strip() if value else value


@register.filter
def indices(value):
    return ", ".join([str(x) for x in range(1, len(value) + 1)])
