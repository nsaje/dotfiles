def get_adjusted_limits_for_additional_rows(target_ids, all_taken_ids, offset, limit):
    limit = limit - len(target_ids)
    offset = max(offset - len(all_taken_ids), 0)
    return offset, limit
