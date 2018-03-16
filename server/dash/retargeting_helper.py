import dash.constants
import dash.models


def can_add_source_with_retargeting(source, ad_group_settings):
    '''
    A new media source can be added if settings don't have retargeting
    enabled or if source supports retargeting.
    '''
    if not ad_group_settings.retargeting_ad_groups and \
            not ad_group_settings.exclusion_retargeting_ad_groups and \
            not ad_group_settings.audience_targeting and \
            not ad_group_settings.exclusion_audience_targeting:
        return True
    return source.can_modify_retargeting_automatically() or\
        source.can_modify_retargeting_manually()


def can_add_sources_with_retargeting(sources, ad_group_settings):
    '''
    A new media source can be added if settings don't have retargeting
    enabled or if source supports retargeting.
    '''
    if not ad_group_settings.retargeting_ad_groups and \
            not ad_group_settings.exclusion_retargeting_ad_groups and \
            not ad_group_settings.audience_targeting and \
            not ad_group_settings.exclusion_audience_targeting:
        return True
    for source in sources:
        if not (source.can_modify_retargeting_automatically() or
                source.can_modify_retargeting_manually()):
            return False
    return True


def supports_retargeting(ad_group_sources):
    '''
    Return true if all active sources on adgroup support retargeting
    '''
    unsupported_sources = []
    for ad_group_source in ad_group_sources:
        if ad_group_source.settings.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue
        if not (ad_group_source.source.can_modify_retargeting_automatically() or
                ad_group_source.source.can_modify_retargeting_manually()):
            unsupported_sources.append(ad_group_source.source)

    return unsupported_sources == [], sorted(unsupported_sources, key=lambda s: s.name)
