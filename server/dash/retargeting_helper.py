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


def supports_retargeting(ad_group):
    '''
    Return true if all active sources on adgroup support retargeting
    '''
    latest_adgroup_source_settings = dash.models.AdGroupSourceSettings.objects.all().filter(
        ad_group_source__ad_group=ad_group
    ).group_current_settings().select_related(
        'ad_group_source'
    )

    unsupported_sources = []
    for adgroup_source_setting in latest_adgroup_source_settings:
        if adgroup_source_setting.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue
        if not (adgroup_source_setting.ad_group_source.source.can_modify_retargeting_automatically() or
                adgroup_source_setting.ad_group_source.source.can_modify_retargeting_manually()):
            unsupported_sources.append(adgroup_source_setting.ad_group_source.source)

    return unsupported_sources == [], sorted(unsupported_sources, key=lambda s: s.name)
