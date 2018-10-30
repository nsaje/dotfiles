from django.db import transaction

import core.models
from core.models.account.exceptions import AccountDoesNotMatch
from dash.features.bulkactions import clonecontent


def clone(request, source_ad_group, campaign, ad_group_name, clone_ads):

    _validate_same_account(source_ad_group, campaign)

    with transaction.atomic():
        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, ad_group_name)
        if clone_ads:
            content_ads = source_ad_group.contentad_set.all().exclude_archived()

            if content_ads.exists():
                # TODO try catch and return a response
                clonecontent.service.clone(request, source_ad_group, content_ads, ad_group)

    return ad_group


def _validate_same_account(source_ad_group, campaign):
    if source_ad_group.campaign.account != campaign.account:
        raise AccountDoesNotMatch(errors={"account": "Can not clone into a different account"})
