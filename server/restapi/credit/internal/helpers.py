import collections


def get_totals_for_credits(credits):
    result = []
    for key, values in _group_by(credits, projection=lambda x: x.currency).items():
        total = sum(credit.effective_amount() for credit in values)
        allocated = sum(credit.get_allocated_amount() for credit in values if not credit.is_past())
        past = sum(credit.effective_amount() for credit in values if credit.is_past())
        result.append(
            {
                "total": total,
                "allocated": allocated,
                "past": past,
                "available": total - allocated - past,
                "currency": key,
            }
        )
    return result


def _group_by(iterable, projection):
    result = collections.defaultdict(list)
    for item in iterable:
        result[projection(item)].append(item)
    return result
