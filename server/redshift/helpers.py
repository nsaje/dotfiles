import sqlparse


def printsql(sql):
    print sqlparse.format(sql, reindent=True, keyword_case='upper')
