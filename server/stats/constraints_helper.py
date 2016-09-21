from utils.queryset_helper import simplify_query

from dash import models

from stats import constants


def narrow_filtered_sources(sources, ad_group_sources):
    sources = sources.filter(
        pk__in=list(ad_group_sources.distinct('source_id').values_list('source_id', flat=True)))
    return simplify_query(sources)


def _get_basic_constraints(start_date, end_date, show_archived, filtered_sources):
    return {
        'date__gte': start_date,
        'date__lte': end_date,
        'show_archived': show_archived,
        'filtered_sources': filtered_sources,
    }


def prepare_all_accounts_constraints(user, breakdown, start_date, end_date, filtered_sources, show_archived=False,
                                     filtered_agencies=None, filtered_account_types=None, only_used_sources=True):

    allowed_accounts = models.Account.objects.all()\
                                             .filter_by_user(user)\
                                             .filter_by_sources(filtered_sources)\
                                             .filter_by_agencies(filtered_agencies)\
                                             .filter_by_account_types(filtered_account_types)
    allowed_campaigns = models.Campaign.objects.all()\
                                               .filter_by_user(user)\
                                               .filter_by_sources(filtered_sources)\
                                               .filter_by_agencies(filtered_agencies)\
                                               .filter_by_account_types(filtered_account_types)

    if constants.get_base_dimension(breakdown) == 'account_id':
        # exclude archived accounts/campaigns only when on accounts tab
        allowed_accounts = allowed_accounts.exclude_archived(show_archived)
        allowed_campaigns = allowed_campaigns.exclude_archived(show_archived)

    constraints = {
        'allowed_accounts': simplify_query(allowed_accounts),
        'allowed_campaigns': simplify_query(allowed_campaigns),
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign__account__in=allowed_accounts)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


def prepare_account_constraints(user, account, breakdown, start_date, end_date, filtered_sources,
                                show_archived=False, only_used_sources=True):
    allowed_campaigns = account.campaign_set.all()\
                                            .filter_by_user(user)\
                                            .filter_by_sources(filtered_sources)

    allowed_ad_groups = models.AdGroup.objects.filter(campaign__in=allowed_campaigns)

    if constants.get_base_dimension(breakdown) == 'campaign_id':
        allowed_campaigns = allowed_campaigns.exclude_archived(show_archived)
        allowed_ad_groups = allowed_ad_groups.exclude_archived(show_archived)

    constraints = {
        'account': account,
        'allowed_campaigns': simplify_query(allowed_campaigns),
        'allowed_ad_groups': simplify_query(allowed_ad_groups),
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign__account_id=account.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


def prepare_campaign_constraints(user, campaign, breakdown, start_date, end_date, filtered_sources,
                                 show_archived=False, only_used_sources=True):
    allowed_ad_groups = campaign.adgroup_set.all().exclude_archived(show_archived)
    constraints = {
        'campaign': campaign,
        'account': campaign.account,
        'allowed_ad_groups': allowed_ad_groups,
        'allowed_content_ads': models.ContentAd.objects.filter(
            ad_group__in=allowed_ad_groups).exclude_archived(show_archived)
    }

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign_id=campaign.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    return constraints


def prepare_ad_group_constraints(user, ad_group, breakdown, start_date, end_date, filtered_sources,
                                 show_archived=False, only_used_sources=True):
    constraints = {
        'ad_group': ad_group,
        'campaign': ad_group.campaign,
        'account': ad_group.campaign.account,
        'allowed_content_ads': models.ContentAd.objects.filter(
            ad_group=ad_group).exclude_archived(show_archived)
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    return constraints
