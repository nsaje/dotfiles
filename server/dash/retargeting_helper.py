def can_add_source_with_retargeting(source, ad_group_settings):
    '''
    A new media source can be added if settings don't have retargeting
    enabled or if source supports retargeting.
    '''
    if ad_group_settings.retargeting_ad_groups == []:
        return True

    return source.can_modify_retargeting_automatically()
