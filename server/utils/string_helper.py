def format_decimal(x, min_decimals, max_decimals):
    assert isinstance(min_decimals, int)
    assert isinstance(max_decimals, int)
    assert min_decimals >= 0 and max_decimals >= 0
    assert min_decimals <= max_decimals

    if max_decimals == 0:
        return str(int(x))

    x = int(x * (10 ** max_decimals)) / (10 ** max_decimals)
    format_str = "%%.%df" % min_decimals
    min_decimals_format = format_str % x
    if len(min_decimals_format) > len(str(x)):
        return min_decimals_format
    else:
        return str(x)
