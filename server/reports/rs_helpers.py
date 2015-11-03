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


def decimal_to_int_exact(num):
    '''
    Converts a decimal.Decimal number to integer.
    Raises decimal.Inexact if non-zero digits were discarded during rounding.
    '''
    if num is None:
        return num
    return int(num.to_integral_exact(context=decimal.Context(traps=[decimal.Inexact])))


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


def count_agr(field_name):
    return 'COUNT("{field_name}")'.format(field_name=field_name)


def count_distinct_agr(field_name):
    return 'COUNT(DISTINCT "{field_name}")'.format(field_name=field_name)


def sum_agr(field_name):
    return 'SUM("{field_name}")'.format(field_name=field_name)


def sum_expr(expr):
    return 'SUM({expr})'.format(expr=expr)


def is_all_null(field_names):
    return 'CASE WHEN ' + ' AND '.join('MAX("{}") IS NULL'.format(f) for f in field_names) + ' THEN 0 ELSE 1 END'


def extract_json_or_null(field_name):
    return "CASE JSON_EXTRACT_PATH_TEXT({field_name}, %s) WHEN '' "\
        "THEN NULL ELSE JSON_EXTRACT_PATH_TEXT({field_name}, %s) END".format(
            field_name=field_name
        )
