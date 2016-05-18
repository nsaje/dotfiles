import collections
import sqlparse

# TODO: find a better solution
from django.db.models.query import QuerySet


def clean_alias(alias):
    # remove order
    return alias.lstrip('+-').strip() if alias else ''


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
    return ((isinstance(value, collections.Iterable) or isinstance(value, QuerySet))
            and type(value) not in (str, unicode))
