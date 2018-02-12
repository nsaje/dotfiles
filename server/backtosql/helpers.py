import collections
import sqlparse

from django.db.models.query import QuerySet
from django.template import loader


class BackToSQLException(Exception):
    pass


def generate_sql(template_name, context, clean=False):
    template = loader.get_template(template_name)
    sql = template.render(context)

    # django templates add some newlines at the end that visually corrupt the sql
    # remove them
    sql = sql.strip()

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


def clean_sql(dirty_sql, single_line=False):
    # removes comments and whitespaces
    sql = sqlparse.format(dirty_sql,
                          reindent=True,
                          keyword_case='upper',
                          identifier_case='lower',
                          strip_comments=True).strip()

    if single_line:
        sql = "".join([" {}".format(x.strip()) for x in sql.splitlines()])
        sql = sql.strip()

    return sql


def clean_prefix(prefix=None):
    if prefix and not prefix.endswith('.'):
        prefix = prefix + '.'
    return prefix or ''


def is_collection(value):
    return (isinstance(value, collections.Iterable) or isinstance(value, QuerySet)) \
        and type(value) not in (str, str)
