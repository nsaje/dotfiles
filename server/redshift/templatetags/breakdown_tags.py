from django.template import Library

from redshift.models import ColumnGroup

register = Library()


@register.filter(name='breakdowns')
def breakdowns(columns):
    return [x for x in columns if x.group == ColumnGroup.BREAKDOWN]


@register.filter(name='aggregates')
def aggregates(columns):
    return [x for x in columns if x.group == ColumnGroup.AGGREGATES]
