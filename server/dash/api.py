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
from dash import publisher_helpers


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


@transaction.atomic
def update_ad_group_source_state(ad_group_source, conf):
    for key, val in conf.items():
        if key in ('cpc_cc', 'daily_budget_cc'):
            conf[key] = converters.cc_to_decimal(val)

    ad_group_source_state = ad_group_source.get_latest_state()

    # determine if we need to update
    need_update = False
    if ad_group_source_state is None:
        need_update = True
    else:
        # we update only if there is a change
        for key, val in conf.items():
            if val is None:
                continue
            if any([
                    key == 'state' and ad_group_source_state.state != val,
                    key == 'cpc_cc' and ad_group_source_state.cpc_cc != val,
                    key == 'daily_budget_cc' and ad_group_source_state.daily_budget_cc != val]):
                    need_update = True
                    break

    # make the changes
    if need_update:
        logger.info('we have to update %s', conf)
        if ad_group_source_state is None:
            new_state = models.AdGroupSourceState(ad_group_source=ad_group_source)
        else:
            new_state = ad_group_source_state
            new_state.pk = None   # create a new state object as a copy of the old one
        for key, val in conf.items():
            if val is None:
                continue
            if key == 'state':
                new_state.state = val
            if key == 'cpc_cc':
                new_state.cpc_cc = val
            if key == 'daily_budget_cc':
                new_state.daily_budget_cc = val
        new_state.save()


@transaction.atomic
def update_publisher_blacklist_state(args):
    _clean_existing_publisher_blacklist(
        args['key'],
        args['level'],
        args['publishers']
    )
    if args['state'] == constants.PublisherStatus.BLACKLISTED:
        _update_publisher_blacklist(
            args['key'],
            args['level'],
            args['publishers']
        )


def _clean_existing_publisher_blacklist(key, level, publishers):
    if level != constants.PublisherBlacklistLevel.GLOBAL:
        if constants.PublisherBlacklistLevel.compare(
                constants.PublisherBlacklistLevel.ACCOUNT,
                level) <= 0:
            account_id = key[0]
            campaign_ids = dash.models.Campaign.objects.filter(
                account_id=account_id
            ).values_list('id', flat=True)

            adgroup_ids = dash.models.AdGroup.objects.filter(
                campaign__id__in=campaign_ids
            ).values_list('id', flat=True)
        elif constants.PublisherBlacklistLevel.compare(
                constants.PublisherBlacklistLevel.CAMPAIGN,
                level) <= 0:
            campaign_id = key[0]
            campaign_adgroup_ids = dash.models.AdGroup.objects.filter(
                campaign__id=campaign_id
            ).values_list('id', flat=True)

    # we always remove relevant blacklist first
    queryset = dash.models.PublisherBlacklist.objects.none()
    for publisher in publishers:
        match_publisher_blacklist = Q(
            name=publisher['domain'],
        )

        if level != constants.PublisherBlacklistLevel.GLOBAL:
            match_publisher_blacklist &= Q(
                source__id=publisher['source_id'],
                source__deprecated=False
            )

        # first delete all associated blacklist entries
        if level == constants.PublisherBlacklistLevel.GLOBAL:
            queryset |= dash.models.PublisherBlacklist.objects.filter(
                match_publisher_blacklist
            )
        else:
            if constants.PublisherBlacklistLevel.compare(
                    constants.PublisherBlacklistLevel.ACCOUNT,
                    level) <= 0:
                queryset |= dash.models.PublisherBlacklist.objects.filter(
                    match_publisher_blacklist &
                    Q(
                        Q(ad_group__id__in=adgroup_ids) |
                        Q(campaign_id__in=campaign_ids) |
                        Q(account_id=account_id)
                    )
                )
            elif constants.PublisherBlacklistLevel.compare(
                    constants.PublisherBlacklistLevel.CAMPAIGN,
                    level) <= 0:
                queryset |= dash.models.PublisherBlacklist.objects.filter(
                    match_publisher_blacklist &
                    Q(
                        Q(ad_group__id__in=campaign_adgroup_ids) |
                        Q(campaign_id=campaign_id)
                    )
                )
            elif constants.PublisherBlacklistLevel.compare(
                    constants.PublisherBlacklistLevel.ADGROUP,
                    level) <= 0:

                ad_group_id = key[0]
                queryset |= dash.models.PublisherBlacklist.objects.filter(
                    match_publisher_blacklist &
                    Q(ad_group__id=ad_group_id)
                )
    queryset.delete()


def _update_publisher_blacklist(key, level, publishers):
    blacklist = []

    already_blacklisted = set([])

    source_cache = {}
    for publisher in publishers:
        # this can be None in case of global pub. blacklisting
        source_id = publisher.get('source_id')
        if level != constants.PublisherBlacklistLevel.GLOBAL:
            if source_id not in source_cache:
                source_cache[source_id] = dash.models.Source.objects.get(id=source_id)
            source = source_cache[source_id]
        else:
            source = None

        blacklist_entry = models.PublisherBlacklist(
            name=publisher['domain'],
            source=source,
            external_id=publisher.get('external_id') or None,
        )

        if level == constants.PublisherBlacklistLevel.GLOBAL:
            blacklist_entry.everywhere = True
        elif level == constants.PublisherBlacklistLevel.ACCOUNT:
            account = dash.models.Account.objects.get(id=key[0])
            blacklist_entry.account = account
        elif level == constants.PublisherBlacklistLevel.CAMPAIGN:
            campaign = dash.models.Campaign.objects.get(id=key[0])
            blacklist_entry.campaign = campaign
        elif level == constants.PublisherBlacklistLevel.ADGROUP:
            ad_group = dash.models.AdGroup.objects.get(id=key[0])
            blacklist_entry.ad_group = ad_group

        blacklist_tuple = (
            level,
            tuple(key) if key is not None else (),
            publisher['domain'],
            source_id,
        )
        if blacklist_tuple in already_blacklisted:
            # skip adding duplicated entries on callback
            continue

        already_blacklisted.add(blacklist_tuple)
        blacklist.append(blacklist_entry)

    if blacklist != []:
        models.PublisherBlacklist.objects.bulk_create(blacklist)


def create_campaign_callback(ad_group_source, source_campaign_key, request):
    ad_group_source.source_campaign_key = source_campaign_key
    ad_group_source.last_successful_sync_dt = datetime.datetime.utcnow()
    ad_group_source.save(request)


def refresh_publisher_blacklist(ad_group_source, request):
    # copy blacklisting information on account and campaign level
    if not ad_group_source.source.can_modify_publisher_blacklist_automatically():
        return

    ad_group = ad_group_source.ad_group
    campaign = ad_group.campaign
    source = ad_group_source.source
    if source.source_type != dash.constants.SourceType.OUTBRAIN:
        current_campaign_blacklist = dash.models.PublisherBlacklist.objects.filter(
            source=source,
            status=dash.constants.PublisherStatus.BLACKLISTED
        ).filter(publisher_helpers.create_queryset_by_key(
            ad_group,
            constants.PublisherBlacklistLevel.CAMPAIGN
        ))
        campaign_blacklisted_publishers = []
        for blacklist_entry in current_campaign_blacklist:
            # setup pending entries
            # create and send blacklist actions
            campaign_blacklisted_publishers.append({
                'domain': blacklist_entry.name,
                'exchange': publisher_helpers.publisher_exchange(source),
                'source_id': source.id,
                'ad_group_id': ad_group.id
            })

        key = [campaign.id]

    current_account_blacklist = dash.models.PublisherBlacklist.objects.filter(
        source=source,
        status=dash.constants.PublisherStatus.BLACKLISTED
    ).filter(publisher_helpers.create_queryset_by_key(
        ad_group,
        constants.PublisherBlacklistLevel.ACCOUNT
    ))

    accountBlacklistedPublishers = []
    for blacklist_entry in current_account_blacklist:
        # setup pending entries
        # create and send blacklist actions
        new_publ = {
            'domain': blacklist_entry.name,
            'exchange': publisher_helpers.publisher_exchange(source),
            'source_id': source.id,
            'ad_group_id': ad_group.id,
        }
        if blacklist_entry.external_id is not None:
            new_publ['external_id'] = blacklist_entry.external_id
        accountBlacklistedPublishers.append(new_publ)

    key = [campaign.account.id]
    if source.source_type == constants.SourceType.OUTBRAIN:
        key.append(campaign.account.outbrain_marketer_id)


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
        k1_helper.update_ad_group(ad_group_source.ad_group_id)


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
