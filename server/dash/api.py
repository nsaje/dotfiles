import newrelic.agent
from django.db import transaction
from django.db.models import Q

from dash import constants
from dash import models
from utils import email_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)


# State of an ad group is set automatically.
# For changes of cpc_cc and daily_budget_cc, mail is sufficient
# There should be no manual actions for
# display_url, brand_name, description and call_to_action
BLOCKED_AD_GROUP_SETTINGS = [
    "state",
    "cpc_cc",
    "max_cpm",
    "daily_budget_cc",
    "display_url",
    "brand_name",
    "description",
    "call_to_action",
    "autopilot_state",
    "autopilot_daily_budget",
]

AUTOMATIC_APPROVAL_OUTBRAIN_ACCOUNT = "0082c33a43e59aa0da8849b5af3448bc7b"


def add_content_ad_sources(ad_group_source):
    if not ad_group_source.source.can_manage_content_ads() or not ad_group_source.can_manage_content_ads:
        return []

    content_ad_sources_added = []
    with transaction.atomic():
        content_ads = models.ContentAd.objects.filter(ad_group=ad_group_source.ad_group)
        for content_ad in content_ads:
            try:
                models.ContentAdSource.objects.get(content_ad=content_ad, source=ad_group_source.source)
            except models.ContentAdSource.DoesNotExist:
                content_ad_source = models.ContentAdSource.objects.create(content_ad, ad_group_source.source)
                content_ad_sources_added.append(content_ad_source)

    return content_ad_sources_added


@newrelic.agent.function_trace()
def update_content_ads_state(content_ads, state, request):
    with transaction.atomic():
        models.ContentAd.objects.filter(id__in=[ca.id for ca in content_ads]).update(state=state)
        content_ad_sources = models.ContentAdSource.objects.filter(
            ~Q(state=state) | ~Q(source_state=state), content_ad_id__in=[ca.id for ca in content_ads]
        )
        content_ad_sources.update(state=state)


def add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request):
    description = "Content ad(s) {{ids}} set to {}.".format(constants.ContentAdSourceState.get_text(state))

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    ad_group.write_history(
        description, user=request.user, action_type=constants.HistoryActionType.CONTENT_AD_STATE_CHANGE
    )

    email_helper.send_ad_group_notification_email(ad_group, request, description)


def add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, archived, request):
    description = "Content ad(s) {{ids}} {}.".format("Archived" if archived else "Restored")

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    ad_group.write_history(
        description, user=request.user, action_type=constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE
    )

    email_helper.send_ad_group_notification_email(ad_group, request, description)


def update_content_ads_archived_state(request, content_ads, ad_group, archived):
    if content_ads.exists():
        add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, archived, request)
        with transaction.atomic():
            for content_ad in content_ads:
                content_ad.archived = archived
                content_ad.save()


def format_bulk_ids_into_description(ids, description_template):
    num_id_limit = 10

    shorten = len(ids) > num_id_limit

    ids_text = "{}{}".format(
        ", ".join(map(str, ids[:num_id_limit])), " and {} more".format(len(ids) - num_id_limit) if shorten else ""
    )

    return description_template.format(ids=ids_text)
