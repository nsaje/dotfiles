import sqlparse

def clean_alias(alias):
    # remove order
    return alias.lstrip('+-') if alias else ''


def get_order(alias):
    if alias.startswith('-'):
        return 'DESC'

    return 'ASC'


def clean_sql(dirty_sql):
    # removes comments and whitespaces
    return sqlparse.format(dirty_sql, strip_comments=True).strip()


def clean_prefix(prefix=None):
    if prefix and not prefix.endswith('.'):
        prefix = prefix + '.'
    return prefix or ''


def printsql(sql):
    print sqlparse.format(sql, reindent=True, keyword_case='upper')
