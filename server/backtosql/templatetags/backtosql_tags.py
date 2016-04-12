from django.template import Library


register = Library()

def _generate(func_name, columns, prefix):
    if getattr(columns, func_name, None) and callable(getattr(columns, func_name, None)):
        return getattr(columns, func_name)(prefix=prefix)
    return ",".join([getattr(x, func_name)(prefix=prefix) for x in columns])


@register.filter
def g(columns, prefix=None):
    return _generate('g', columns, prefix=prefix)


@register.filter
def g_alias(columns, prefix=None):
    return _generate('g_alias', columns, prefix=prefix)


@register.filter
def g_w_alias(columns, prefix=None):
    return _generate('g_w_alias', columns, prefix=prefix)


@register.filter
def lspace(value):
    return " " + str(value).strip() if value else value


@register.filter
def _as_(value):
    return " AS " + str(value).strip() if value else value