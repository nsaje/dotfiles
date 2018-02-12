from django.db.models import Q

from . import models, constants
import dash.constants

_FIELD_MAPPER = {
    'content_ad': 'content_ad_id',
    'ad_group': 'content_ad__ad_group_id',
    'campaign': 'content_ad__ad_group__campaign_id',
    'account': 'content_ad__ad_group__campaign__account_id',
    'agency': 'content_ad__ad_group__campaign__account__agency_id',
}


def filter_valid_content_ad_sources(content_ad_sources):
    valid = []
    lookup = {}
    for cas in content_ad_sources:
        for entity_short, entity_long in _FIELD_MAPPER.items():
            if cas[entity_long]:
                lookup.setdefault(entity_short + '_id__in', set()).add(cas[entity_long])
    applied_filters = _get_any_applied_filters(lookup)
    for cas in content_ad_sources:
        is_valid = cas['source__content_ad_submission_policy'] == dash.constants.SourceSubmissionPolicy.AUTOMATIC
        for entity_short, entity_long in _FIELD_MAPPER.items():
            submission_filter = applied_filters.get((cas['source_id'], entity_short, cas[entity_long]))
            if not submission_filter:
                continue
            if is_valid and submission_filter.state == constants.SubmissionFilterState.BLOCK:
                is_valid = False
                break
            if not is_valid and submission_filter.state == constants.SubmissionFilterState.ALLOW:
                is_valid = True
                break
        if is_valid:
            valid.append(cas)
    return valid


def _get_any_applied_filters(lookup):
    if not lookup:
        return {}
    lookup_map = {}
    rules = Q()
    for key, value in lookup.items():
        rules |= Q(**{key: value})
    for submission_filter in models.SubmissionFilter.objects.filter(rules):
        lookup_map[submission_filter.get_lookup_key()] = submission_filter
    return lookup_map
