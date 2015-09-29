import decimal


def unchanged(val):
    return val


def from_micro_cpm(num):
    if num is None:
        return None
    else:
        # we divide first by a million (since we use fixed point) and then by additional thousand (cpm)
        return num * 1.0 / 1000000000


def from_cc(num):
    if num is None:
        return None

    return float(decimal.Decimal(round(num)) / decimal.Decimal(10000))


def to_percent(num):
    if num is None:
        return None
    else:
        return num * 100


def sum_div(expr, divisor):
    return ('CASE WHEN SUM("{divisor}") <> 0 THEN SUM(CAST("{expr}" AS FLOAT)) / SUM("{divisor}") '
            'ELSE NULL END').format(
                expr=expr,
                divisor=divisor,)


def click_discrepancy(clicks_col, visits_col):
    return ('CASE WHEN SUM("{clicks}") = 0 THEN NULL WHEN SUM("{visits}") = 0 THEN 1'
            ' WHEN SUM("{clicks}") < SUM("{visits}") THEN 0'
            ' ELSE (SUM(CAST("{clicks}" AS FLOAT)) - SUM("{visits}")) / SUM("{clicks}")'
            ' END').format(
                clicks=clicks_col,
                visits=visits_col)


def sum_agr(expr):
    return 'SUM("{expr}")'.format(expr=expr)


def is_all_null(field_names):
    return 'CASE WHEN ' + ' AND '.join('MAX("{}") IS NULL'.format(f) for f in field_names) + ' THEN 0 ELSE 1 END'
