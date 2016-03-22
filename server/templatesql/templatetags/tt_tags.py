from django.template import Library

register = Library()

# TODO: rename to rs_tags
@register.filter(name='prefix')
def prefix(columns, arg):
    #TODO: if only one column
    return [x.gen(prefix=arg) for x in columns]


@register.filter(name='indices')
def indices(value, start=1):
    return range(start, len(value) + 1)