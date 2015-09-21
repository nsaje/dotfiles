
def from_micro_cpm(num):
    if num is None:
        return None
    else:
        # we divide first by a million (since we use fixed point) and then by additional thousand (cpm)
        return num * 1.0 / 1000000000

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
