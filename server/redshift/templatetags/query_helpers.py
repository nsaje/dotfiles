
from django.template import Library

register = Library()


@register.filter(name='pfx')
def pfx(columns, arg):
    return [x.pfx(arg) for x in columns]
