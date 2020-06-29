from django.db import transaction

import core.models
import dash.features.clonecontentad
from core.models.account.exceptions import AccountDoesNotMatch


def clone(request, source_ad_group, campaign, ad_group_name, clone_ads, state_override=None, ad_state_override=None):

    _validate_same_account(source_ad_group, campaign)

    with transaction.atomic():
        ad_group = core.models.AdGroup.objects.clone(
            request, source_ad_group, campaign, ad_group_name, state_override=state_override
        )
        if clone_ads:
            content_ads = source_ad_group.contentad_set.all().exclude_archived()

            if content_ads.exists():
                dash.features.clonecontentad.service.clone(
                    request, source_ad_group, content_ads, ad_group, state_override=ad_state_override
                )

    return ad_group


def _validate_same_account(source_ad_group, campaign):
    if source_ad_group.campaign.account != campaign.account:
        raise AccountDoesNotMatch(errors={"account": "Can not clone into a different account"})
