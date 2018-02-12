from . import model


def _get_flags_map():
    return {flag.id: flag for flag in model.CustomFlag.objects.all()}


def _get_source(flag_id):
    if flag_id.startswith('b1_'):
        return 'RTB'
    if flag_id.startswith('api_'):
        return 'API'
    if flag_id.startswith('yahoo_'):
        return 'Yahoo'
    if flag_id.startswith('ob_'):
        return 'Outbrain'
    return 'All'


def _get_flags_dict_list(flags_map, entity, level):
    flags_dict_list = []
    for flag_id, flag_value in (entity.custom_flags or {}).items():
        if not flag_value or flag_id not in flags_map:
            continue
        flag = flags_map[flag_id]
        flags_dict_list.append({
            'summary': flag.name,
            'level': level,
            'source': _get_source(flag_id),
            'details': flag.description or None,
            'confirmed': True,
        })
    return flags_dict_list


def get_all_custom_flags_on_ad_group(ad_group, flags_map=None):
    if not flags_map:
        flags_map = _get_flags_map()
    return _get_flags_dict_list(flags_map, ad_group, 'Ad group') + get_all_custom_flags_on_campaign(ad_group.campaign, flags_map)


def get_all_custom_flags_on_campaign(campaign, flags_map=None):
    if not flags_map:
        flags_map = _get_flags_map()
    return _get_flags_dict_list(flags_map, campaign, 'Campaign') + get_all_custom_flags_on_account(campaign.account, flags_map)


def get_all_custom_flags_on_account(account, flags_map=None):
    if not flags_map:
        flags_map = _get_flags_map()
    agency_flags_dict_list = get_all_custom_flags_on_agency(account.agency, flags_map) if account.agency else []
    return _get_flags_dict_list(flags_map, account, 'Account') + agency_flags_dict_list


def get_all_custom_flags_on_agency(agency, flags_map=None):
    if not flags_map:
        flags_map = _get_flags_map()
    return _get_flags_dict_list(flags_map, agency, 'Agency')
