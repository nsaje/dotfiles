import dash.constants
import dash.models


def supports_retargeting(ad_group_sources):
    """
    Return true if all active sources on adgroup support retargeting
    """
    unsupported_sources = []
    for ad_group_source in ad_group_sources:
        if ad_group_source.settings.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue
        if not (ad_group_source.source.can_modify_retargeting_automatically()):
            unsupported_sources.append(ad_group_source.source)

    return unsupported_sources == [], sorted(unsupported_sources, key=lambda s: s.name)
