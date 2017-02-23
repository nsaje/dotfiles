import datetime
import decimal
import logging
import newrelic.agent

from django.db import transaction
from django.db.models import Q

import dash.models
from utils import redirector_helper
from utils import email_helper
from utils import k1_helper
from utils import converters

from dash import models
from dash import constants


logger = logging.getLogger(__name__)


# State of an ad group is set automatically.
# For changes of cpc_cc and daily_budget_cc, mail is sufficient
# There should be no manual actions for
# display_url, brand_name, description and call_to_action
BLOCKED_AD_GROUP_SETTINGS = [
    'state', 'cpc_cc', 'max_cpm', 'daily_budget_cc', 'display_url',
    'brand_name', 'description', 'call_to_action',
    'autopilot_state', 'autopilot_daily_budget', 'landing_mode',
]

AUTOMATIC_APPROVAL_OUTBRAIN_ACCOUNT = '0082c33a43e59aa0da8849b5af3448bc7b'


def add_content_ad_sources(ad_group_source):
    if not ad_group_source.source.can_manage_content_ads() or not ad_group_source.can_manage_content_ads:
        return []

    content_ad_sources_added = []
    with transaction.atomic():
        content_ads = models.ContentAd.objects.filter(ad_group=ad_group_source.ad_group)

        for content_ad in content_ads:
            try:
                content_ad_source = models.ContentAdSource.objects.get(
                    content_ad=content_ad,
                    source=ad_group_source.source
                )
            except models.ContentAdSource.DoesNotExist:
                content_ad_source = models.ContentAdSource.objects.create(
                    source=ad_group_source.source,
                    content_ad=content_ad,
                    submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                    state=content_ad.state
                )
                content_ad_sources_added.append(content_ad_source)

    return content_ad_sources_added


def update_ad_group_redirector_settings(ad_group, ad_group_settings):
    campaign_settings = ad_group.campaign.get_current_settings()
    redirector_helper.insert_adgroup(
        ad_group,
        ad_group_settings,
        campaign_settings,
    )


@newrelic.agent.function_trace()
def update_content_ads_state(content_ads, state, request):
    with transaction.atomic():
        models.ContentAd.objects.filter(id__in=[ca.id for ca in content_ads]).update(state=state)
        content_ad_sources = models.ContentAdSource.objects.filter(
            ~Q(state=state) | ~Q(source_state=state),
            content_ad_id__in=[ca.id for ca in content_ads],
        )
        content_ad_sources.update(state=state)


def add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request):
    description = 'Content ad(s) {{ids}} set to {}.'.format(constants.ContentAdSourceState.get_text(state))

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    ad_group.write_history(
        description,
        user=request.user,
        action_type=constants.HistoryActionType.CONTENT_AD_STATE_CHANGE
    )

    email_helper.send_ad_group_notification_email(ad_group, request, description)


def add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, archived, request):
    description = 'Content ad(s) {{ids}} {}.'.format('Archived' if archived else 'Restored')

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    ad_group.write_history(
        description,
        user=request.user,
        action_type=constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE
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

    ids_text = '{}{}'.format(', '.join(map(str, ids[:num_id_limit])),
                             ' and {} more'.format(len(ids) - num_id_limit) if shorten else '')

    return description_template.format(ids=ids_text)


def set_ad_group_source_settings(
    ad_group_source,
    settings_obj,
    request,
    system_user=None,
    landing_mode=None,
    ping_k1=True
):
    latest_settings = ad_group_source.get_current_settings()

    state = settings_obj.get('state')
    cpc_cc = settings_obj.get('cpc_cc')
    daily_budget_cc = settings_obj.get('daily_budget_cc')

    assert cpc_cc is None or isinstance(cpc_cc, decimal.Decimal)
    assert daily_budget_cc is None or isinstance(daily_budget_cc, decimal.Decimal)

    if not _has_any_ad_group_source_setting_changed(latest_settings, state, cpc_cc, daily_budget_cc, landing_mode):
        return
    _update_ad_group_source_setting(
        ad_group_source,
        request,
        latest_settings,
        settings_obj,
        state,
        cpc_cc,
        daily_budget_cc,
        landing_mode,
        system_user=system_user
    )

    if ping_k1:
        k1_helper.update_ad_group(ad_group_source.ad_group_id, msg="dash.api.set_ad_group_source_settings")


def _has_any_ad_group_source_setting_changed(latest_settings, state, cpc_cc, daily_budget_cc, landing_mode):
    if state is not None and state != latest_settings.state:
        return True

    if cpc_cc is not None and cpc_cc != latest_settings.cpc_cc:
        return True

    if daily_budget_cc is not None and daily_budget_cc != latest_settings.daily_budget_cc:
        return True

    if landing_mode is not None and landing_mode != latest_settings.landing_mode:
        return True

    return False


def _update_ad_group_source_setting(
    ad_group_source,
    request,
    latest_settings,
    settings_obj,
    state,
    cpc_cc,
    daily_budget_cc,
    landing_mode,
    system_user=None
):
    new_settings = latest_settings.copy_settings()
    old_settings_obj = {}
    if state is not None:
        new_settings.state = state
    if cpc_cc is not None:
        old_settings_obj['cpc_cc'] = latest_settings.cpc_cc
        new_settings.cpc_cc = cpc_cc
    if daily_budget_cc is not None:
        old_settings_obj['daily_budget_cc'] = latest_settings.daily_budget_cc
        new_settings.daily_budget_cc = daily_budget_cc
    if landing_mode is not None:
        new_settings.landing_mode = landing_mode
    if not request:
        new_settings.system_user = system_user
    else:
        new_settings.created_by = request.user
    new_settings.save(request, action_type=constants.HistoryActionType.MEDIA_SOURCE_SETTINGS_CHANGE)
    _notify_ad_group_source_settings_changed(ad_group_source, settings_obj, old_settings_obj, request)
    return new_settings


def _notify_ad_group_source_settings_changed(ad_group_source, change_obj, old_change_obj, request):
    if not request:
        return

    changes_text_parts = []
    for key, val in change_obj.items():
        if val is None:
            continue
        field = models.AdGroupSettings.get_human_prop_name(key)
        val = models.AdGroupSettings.get_human_value(key, val)
        source_name = ad_group_source.source.name
        old_val = old_change_obj.get(key)
        if old_val is None:
            text = '%s %s set to %s' % (source_name, field, val)
        else:
            old_val = models.AdGroupSettings.get_human_value(key, old_val)
            text = '%s %s set from %s to %s' % (source_name, field, old_val, val)
        changes_text_parts.append(text)

    email_helper.send_ad_group_notification_email(
        ad_group_source.ad_group, request, '\n'.join(changes_text_parts))
