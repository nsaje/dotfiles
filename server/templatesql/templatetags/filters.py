from django.template import Library

register = Library()


@register.filter(name='prefix')
def prefix(columns, arg):
    return [x.pfx(arg) for x in columns]
