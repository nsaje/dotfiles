import bluekaiapi


def get_reach(expression):
    try:
        # TODO: Caching
        reach = bluekaiapi.get_segment_reach(expression)
        return {
            'value': reach,
            'relative': calculate_relative_reach(reach)
        }
    except Exception:
        return None


def calculate_relative_reach(reach):
    if not reach:
        return 0

    x = float(reach) / pow(10, 7)
    relative = 1 - (1 / (x + 1))
    return int(relative * 100)
