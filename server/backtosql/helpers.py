import collections
import sqlparse

from django.db.models.query import QuerySet
from django.template import loader


class BackToSQLException(Exception):
    pass


def generate_sql(template_name, context):
    template = loader.get_template(template_name)
    return clean_sql(template.render(context))


def clean_alias(alias):
    # remove order
    return alias.strip().lstrip('+-') if alias else ''


def get_order(alias):
    if alias.startswith('-'):
        return 'DESC'

    return 'ASC'


def clean_sql(dirty_sql):
    # removes comments and whitespaces
    return sqlparse.format(dirty_sql, reindent=True, keword_case='upper', strip_comments=True).strip()


def clean_prefix(prefix=None):
    if prefix and not prefix.endswith('.'):
        prefix = prefix + '.'
    return prefix or ''


def printsql(sql, params=None, cursor=None):
    if cursor:
        sql = cursor.mogrify(sql, params)
    sql = sqlparse.format(sql,
                          reindent=True,
                          indent_tabs=False,
                          indent_width=1,
                          keyword_case='upper',
                          identifier_case='lower',
                          strip_comments=True).strip()

    print('\033[92m' + sql + '\033[0m')


def is_collection(value):
    return (isinstance(value, collections.Iterable) or isinstance(value, QuerySet)) \
        and type(value) not in (str, unicode)
