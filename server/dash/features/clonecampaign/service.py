from django.db import transaction

import core.models
import dash.features.cloneadgroup.service
import dash.views.helpers
import utils.email_helper
from server import celery

from . import exceptions


def clone(
    request,
    source_campaign,
    destination_campaign_name,
    clone_ad_groups,
    clone_ads,
    ad_group_state_override=None,
    ad_state_override=None,
    send_email=False,
):
    with transaction.atomic():
        if clone_ads and not clone_ad_groups:
            raise exceptions.CanNotCloneAds("Can't clone ads if ad group is not cloned.")

        cloned_campaign = core.models.Campaign.objects.clone(request, source_campaign, destination_campaign_name)

        if clone_ad_groups:
            source_ad_groups = source_campaign.adgroup_set.all().exclude_archived()

            for source_ad_group in source_ad_groups:
                dash.features.cloneadgroup.service.clone(
                    request,
                    source_ad_group,
                    cloned_campaign,
                    source_ad_group.name,
                    clone_ads,
                    ad_group_state_override,
                    ad_state_override,
                )

    return cloned_campaign


@celery.app.task(acks_late=True, name="campaign_cloning", soft_time_limit=39 * 60)
def clone_async(
    request,
    source_campaign_id,
    destination_campaign_name,
    clone_ad_groups,
    clone_ads,
    ad_group_state_override=None,
    ad_state_override=None,
    send_email=False,
):
    try:
        source_campaign = dash.views.helpers.get_campaign(request.user, source_campaign_id)
        cloned_campaign = clone(
            request,
            source_campaign,
            destination_campaign_name,
            clone_ad_groups,
            clone_ads,
            ad_group_state_override,
            ad_state_override,
        )
        if send_email:
            utils.email_helper.send_campaign_cloned_success_email(request, source_campaign.name, cloned_campaign.name)

    except Exception as err:
        if send_email:
            utils.email_helper.send_campaign_cloned_error_email(
                request, source_campaign.name, destination_campaign_name
            )
        raise err

    return cloned_campaign.id
