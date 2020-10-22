from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest

import core.models
import dash.features.clonecontentad
import utils.email_helper
import utils.exc
import zemauth.access
from core.models.account.exceptions import AccountDoesNotMatch
from server import celery
from zemauth.features.entity_permission import Permission


def clone(
    request,
    source_ad_group,
    destination_campaign,
    destination_ad_group_name,
    clone_ads,
    ad_group_state_override=None,
    ad_state_override=None,
):
    _validate_same_account(source_ad_group, destination_campaign)
    with transaction.atomic():
        ad_group = core.models.AdGroup.objects.clone(
            request,
            source_ad_group,
            destination_campaign,
            destination_ad_group_name,
            state_override=ad_group_state_override,
        )
        if clone_ads:
            content_ads = source_ad_group.contentad_set.all().exclude_archived()

            if content_ads.exists():
                dash.features.clonecontentad.service.clone(
                    request, source_ad_group, content_ads, ad_group, state_override=ad_state_override
                )

    return ad_group


@celery.app.task(acks_late=True, name="ad_group_cloning", soft_time_limit=39 * 60)
def clone_async(
    user,
    source_ad_group_id,
    source_ad_group_name,
    destination_ad_group_name,
    destination_campaign_id,
    clone_ads,
    ad_group_state_override=None,
    ad_state_override=None,
    send_email=False,
):
    request = HttpRequest()
    request.user = user
    try:
        source_ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, source_ad_group_id)
        destination_campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, destination_campaign_id)
        cloned_ad_group = clone(
            request,
            source_ad_group,
            destination_campaign,
            destination_ad_group_name,
            clone_ads,
            ad_group_state_override,
            ad_state_override,
        )
        if send_email:
            utils.email_helper.send_ad_group_cloned_success_email(request, source_ad_group.name, cloned_ad_group.name)

        return cloned_ad_group.id

    except ValidationError as err:
        if send_email:
            utils.email_helper.send_ad_group_cloned_error_email(
                request, source_ad_group_name, destination_ad_group_name, err.message
            )

    except Exception as err:
        if send_email:
            utils.email_helper.send_ad_group_cloned_error_email(
                request, source_ad_group_name, destination_ad_group_name
            )
        raise err


def _validate_same_account(source_ad_group, campaign):
    if source_ad_group.campaign.account != campaign.account:
        raise AccountDoesNotMatch(errors={"account": "Can not clone into a different account"})
