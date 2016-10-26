import collections
import sqlparse

from django.db.models.query import QuerySet
from django.template import loader


class BackToSQLException(Exception):
    pass


def generate_sql(template_name, context, clean=False):
    template = loader.get_template(template_name)
    sql = template.render(context)

    # clean affects performance so you might not want to use it if not needed
    if clean:
        return clean_sql(sql)

    return sql


def clean_alias(alias):
    # remove order
    return alias.strip().lstrip('+-') if alias else ''


def get_order(alias, nulls=None):
    properties = ''
    if nulls and nulls.upper() == 'LAST':
        properties = ' NULLS LAST'
    elif nulls and nulls.upper() == 'FIRST':
        properties = ' NULLS FIRST'

    if alias.startswith('-'):
        return 'DESC' + properties

    return 'ASC' + properties


def clean_sql(dirty_sql):
    # removes comments and whitespaces
    return sqlparse.format(dirty_sql, reindent=True, keyword_case='upper', strip_comments=True).strip()


def clean_prefix(prefix=None):
    if prefix and not prefix.endswith('.'):
        prefix = prefix + '.'
    return prefix or ''


def is_collection(value):
    return (isinstance(value, collections.Iterable) or isinstance(value, QuerySet)) \
        and type(value) not in (str, unicode)
