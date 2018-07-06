import decimal


def default_currency(number, places=2):
    return format_currency(number, places=places, curr='$')


def format_currency(value,
                    *,
                    places=2,
                    rounding=decimal.ROUND_HALF_DOWN,
                    curr='',
                    sep=',',
                    dp='.',
                    pos='',
                    neg='-',
                    trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    rounding:optional rounding with set default (must be a decimal constant)
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank
    """
    value = decimal.Decimal(value)
    q = decimal.Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q, rounding).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places != 0:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))
