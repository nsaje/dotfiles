from collections import defaultdict
import datetime
import decimal
import logging
import newrelic.agent

from django.db import transaction, IntegrityError
from django.db.models import Q

import actionlog.api
import actionlog.api_contentads
import actionlog.models
import actionlog.constants
import dash.models
import utils.exc
from utils import redirector_helper
from utils import email_helper

from dash import exc
from dash import models
from dash import constants
from dash import regions
from dash import consistency

import utils.url_helper

logger = logging.getLogger(__name__)


# State of an ad group is set automatically.
# For changes of cpc_cc and daily_budget_cc, mail is sufficient
# There should be no manual actions for
# display_url, brand_name, description and call_to_action
BLOCKED_AD_GROUP_SETTINGS = [
    'state', 'cpc_cc', 'daily_budget_cc', 'display_url',
    'brand_name', 'description', 'call_to_action',
]

AUTOMATIC_APPROVAL_OUTBRAIN_ACCOUNT = '0082c33a43e59aa0da8849b5af3448bc7b'


def cc_to_decimal(val_cc):
    if val_cc is None:
        return None
    return decimal.Decimal(val_cc) / 10000


@transaction.atomic
def update_ad_group_source_state(ad_group_source, conf):
    for key, val in conf.items():
        if key in ('cpc_cc', 'daily_budget_cc'):
            conf[key] = cc_to_decimal(val)

    ad_group_source_state = _get_latest_ad_group_source_state(ad_group_source)

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
                    key == 'daily_budget_cc' and ad_group_source_state.daily_budget_cc != val,
                    key == 'publisher_blacklist',
                ]):
                    need_update = True
                    break

    # make the changes
    if need_update:
        logger.info('we have to update %s', conf)
        if ad_group_source_state is None:
            new_state = models.AdGroupSourceState.objects.create(ad_group_source=ad_group_source)
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
            if key == 'publisher_blacklist':
                _update_publisher_blacklist_state(ad_group_source, val)

        new_state.save()


def _update_publisher_blacklist_state(ad_group_source, conf):
    source_cache = {}
    blacklist_list = []
    for pub_blacklist in conf['blacklist']:
        ad_group = ad_group_source.ad_group
        source_slug = pub_blacklist['exchange']
        if source_slug not in source_cache:
            source_cache[source_slug] =\
                models.Source.objects.filter(tracking_slug__endswith=source_slug).first()

        if not source_cache[source_slug]:
            raise Exception('Invalid tracking slug {}'.format(source_slug or ''))

        # store blacklisted publishers and push to other sources
        blacklist_list.append(
            models.PublisherBlacklist(
                name=pub_blacklist['domain'],
                ad_group=ad_group,
                source=source_cache[source_slug]
            )
        )
    state = conf['state']
    if state == constants.PublisherStatus.BLACKLISTED:
        models.PublisherBlacklist.objects.bulk_create(blacklist_list)
    elif state == constants.PublisherStatus.ENABLED:
        query_set = models.PublisherBlacklist.objects.none()
        for pub_blacklist in blacklist_list:
            query_set = query_set | models.PublisherBlacklist.objects.filter(
                name=pub_blacklist.name,
                ad_group=pub_blacklist.ad_group,
                source=pub_blacklist.source
            )
        query_set.delete()
    else:
        raise Exception("Not implemented")


def _get_latest_ad_group_source_state(ad_group_source):
    try:
        agss = models.AdGroupSourceState.objects.filter(ad_group_source=ad_group_source).latest()
        return agss
    except models.AdGroupSourceState.DoesNotExist:
        return None


def create_campaign_callback(ad_group_source, source_campaign_key, request):
    ad_group_source.source_campaign_key = source_campaign_key
    ad_group_source.last_successful_sync_dt = datetime.datetime.utcnow()
    ad_group_source.save(request)


def order_additional_updates_after_campaign_creation(ad_group_source, request):
    ad_group_settings = ad_group_source.ad_group.get_current_settings()
    source = ad_group_source.source

    if can_modify_selected_target_regions_manually(
            source, ad_group_settings.targets_countries(), ad_group_settings.targets_dma()):

        new_field_value = _get_manual_action_target_regions_value(
            ad_group_source,
            ad_group_settings.target_regions,
            ad_group_settings.targets_countries(),
            ad_group_settings.targets_dma()
        )

        actionlog.api.init_set_ad_group_manual_property(
            ad_group_source,
            request,
            'target_regions',
            new_field_value
        )

    # update ad group source settings
    cons = consistency.SettingsStateConsistence(ad_group_source)
    settings_changes = cons.get_needed_state_updates()
    if settings_changes:
        actionlog.api.set_ad_group_source_settings(settings_changes, ad_group_source, request=request, send=True)


def insert_content_ad_callback(
        ad_group_source,
        content_ad_source,
        source_content_ad_id,
        source_state,
        submission_status,
        submission_errors
):
    if source_content_ad_id is not None:
        source_content_ad_id = str(source_content_ad_id)

    content_ad_source.source_content_ad_id = source_content_ad_id
    content_ad_source.source_state = source_state

    if submission_status is not None:
        _update_content_ad_source_submission_status(content_ad_source, submission_status)
        content_ad_source.submission_errors = submission_errors

    content_ad_source.save()


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


def submit_ad_group_callback(ad_group_source, source_content_ad_id, submission_status, submission_errors):
    if ad_group_source.source.content_ad_submission_type != constants.SourceSubmissionType.AD_GROUP:
        raise Exception('Invalid source submission type')

    actions = []
    with transaction.atomic():
        ad_group_source.source_content_ad_id = source_content_ad_id
        ad_group_source.submission_status = submission_status
        ad_group_source.submission_errors = submission_errors
        ad_group_source.save(None)

        if submission_status != constants.ContentAdSubmissionStatus.PENDING and\
           submission_status != constants.ContentAdSubmissionStatus.APPROVED and\
           submission_status != constants.ContentAdSubmissionStatus.REJECTED:
            return

        content_ad_sources = list(
            models.ContentAdSource.objects.filter(
                Q(source_content_ad_id__isnull=True) | Q(source_content_ad_id=''),
                content_ad__ad_group=ad_group_source.ad_group,
                source=ad_group_source.source,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED
            )
        )

        for content_ad_source in content_ad_sources:
            content_ad_source.source_content_ad_id = source_content_ad_id
            content_ad_source.submission_status = submission_status
            content_ad_source.save()

        for content_ad_source in content_ad_sources:
            actions.append(
                actionlog.api_contentads.init_insert_content_ad_action(
                    content_ad_source,
                    request=None,
                    send=False
                )
            )

    return actions


def submit_content_ads(content_ad_sources, request):
    actions = []

    by_ags = defaultdict(list)
    for content_ad_source in content_ad_sources:
        if content_ad_source.submission_status != constants.ContentAdSubmissionStatus.NOT_SUBMITTED:
            continue

        k = (content_ad_source.content_ad.ad_group_id, content_ad_source.source_id)
        by_ags[k].append(content_ad_source)

    with transaction.atomic():
        for key, ags_content_ad_sources in by_ags.iteritems():
            if not ags_content_ad_sources:
                continue

            ad_group_id, source_id = key
            ad_group_source = models.AdGroupSource.objects.select_related('source').get(
                ad_group_id=ad_group_id,
                source_id=source_id
            )

            if ad_group_source.source.content_ad_submission_type == constants.SourceSubmissionType.BATCH:
                batch_ids = []

                for content_ad_source in ags_content_ad_sources:
                    batch = content_ad_source.content_ad.batch

                    if batch.id in batch_ids:
                        continue

                    batch_ids.append(batch.id)
                    actions.append(actionlog.api_contentads.init_insert_content_ad_batch(
                        batch, content_ad_source.source, request, send=False))

                continue

            if ad_group_source.source.content_ad_submission_type == constants.SourceSubmissionType.AD_GROUP:
                if actionlog.models.ActionLog.objects.filter(
                        ad_group_source=ad_group_source,
                        action=actionlog.constants.Action.SUBMIT_AD_GROUP,
                        state=actionlog.constants.ActionState.WAITING,
                ).exists():
                    continue

                if ad_group_source.submission_status == constants.ContentAdSubmissionStatus.NOT_SUBMITTED:
                    actions.append(
                        actionlog.api_contentads.init_submit_ad_group_action(
                            ad_group_source,
                            ags_content_ad_sources[0],
                            request,
                            send=False
                        )
                    )
                    continue

                if ad_group_source.submission_status != constants.ContentAdSubmissionStatus.PENDING and\
                   ad_group_source.submission_status != constants.ContentAdSubmissionStatus.APPROVED and\
                   ad_group_source.submission_status != constants.ContentAdSubmissionStatus.REJECTED:
                    continue

                for content_ad_source in ags_content_ad_sources:
                    content_ad_source.source_content_ad_id = ad_group_source.source_content_ad_id
                    content_ad_source.submission_status = ad_group_source.submission_status
                    content_ad_source.save()

            for content_ad_source in ags_content_ad_sources:
                actions.append(
                    actionlog.api_contentads.init_insert_content_ad_action(
                        content_ad_source,
                        request,
                        send=False
                    )
                )

    return actions


@transaction.atomic()
def update_content_ads_submission_status(ad_group_source, request=None):
    if ad_group_source.source.content_ad_submission_type != constants.SourceSubmissionType.AD_GROUP:
        return []

    content_ad_sources = models.ContentAdSource.objects.filter(
        content_ad__ad_group_id=ad_group_source.ad_group_id,
        source_id=ad_group_source.source_id,
        submission_status__in=[constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                               constants.ContentAdSubmissionStatus.PENDING]
    )
    content_ad_sources_ids = [cas.id for cas in content_ad_sources]

    content_ad_sources.update(
        source_content_ad_id=ad_group_source.source_content_ad_id,
        submission_status=ad_group_source.submission_status,
    )

    actions = []
    for cas in models.ContentAdSource.objects.filter(id__in=content_ad_sources_ids):
        changes = {
            'state': cas.state,
        }

        actions.append(
            actionlog.api_contentads.init_update_content_ad_action(
                cas,
                changes,
                request=request,
                send=False,
            )
        )

    return actions


@transaction.atomic()
def update_multiple_content_ad_source_states(ad_group_source, content_ad_data):
    """ Returns update_content_ad actions for content_ad_sources
    that are not in sync with external systems. """
    content_ad_sources = {}

    for content_ad_source in models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group_source.ad_group,
            source=ad_group_source.source):
        content_ad_sources[content_ad_source.get_source_id()] = content_ad_source

    unsynced_content_ad_sources_actions = []

    for data in content_ad_data:
        content_ad_source = content_ad_sources.get(data['id'])

        if content_ad_source is None:
            continue

        changed = False

        if data['state'] != content_ad_source.source_state:
            content_ad_source.source_state = data['state']
            changed = True

        if data['state'] != content_ad_source.content_ad.state:
            logger.info(
                'Found inconsistent content ad state on media source %s for content ad %d: source state=%d, z1 state=%d, source submission status=%d, z1 submission status=%d',
                content_ad_source.source.name, content_ad_source.content_ad.pk,
                data.get('state'), content_ad_source.content_ad.state,
                data.get('submission_status'), content_ad_source.submission_status,
            )

        if 'submission_status' in data and data['submission_status'] != content_ad_source.submission_status:
            is_unsynced = all([
                data['submission_status'] == constants.ContentAdSubmissionStatus.APPROVED,
                content_ad_source.content_ad.state != data['state'],
            ])
            if is_unsynced:
                # Content ad state was not synced with media source
                unsynced_content_ad_sources_actions.append(
                    (content_ad_source, {'state': content_ad_source.content_ad.state})
                )

            if _update_content_ad_source_submission_status(content_ad_source, data['submission_status']):
                changed = True

        if 'submission_errors' in data and data['submission_errors'] != content_ad_source.submission_errors:
            content_ad_source.submission_errors = data['submission_errors']
            changed = True

        if changed:
            content_ad_source.save()

    if unsynced_content_ad_sources_actions:
        logger.info(
            'Found unsynced content ads for ad group %s on sources: %s',
            ad_group_source.ad_group,
            ', '.join(set(action[0].source.name for action in unsynced_content_ad_sources_actions))
        )
        return actionlog.api_contentads.init_bulk_update_content_ad_actions(
            unsynced_content_ad_sources_actions, None)

    return []


def update_content_ad_source_state(content_ad_source, data):
    state = data.get('source_state')
    submission_status = data.get('submission_status')

    if state:
        content_ad_source.source_state = state

    if submission_status:
        _update_content_ad_source_submission_status(content_ad_source, submission_status)

    content_ad_source.save()


def order_ad_group_settings_update(ad_group, current_settings, new_settings, request, send=True,
                                   iab_update=False, redirects_update=False):
    changes = current_settings.get_setting_changes(new_settings)

    campaign_settings = ad_group.campaign.get_current_settings()
    # TODO: temporary hack to prevent changing IAB category every time settings
    # update is called - this should be moved to adgroup settings
    if iab_update:
        changes['iab_category'] = campaign_settings.iab_category

    if redirects_update:
        # TODO: temporary hack to force ad group insertion into redirector
        changes['tracking_code'] = new_settings.get_tracking_codes()

    if not changes:
        return []

    order = actionlog.models.ActionLogOrder.objects.create(
        order_type=actionlog.constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
    )

    if any(prop in changes for prop in
           ['tracking_code', 'enable_ga_tracking', 'enable_adobe_tracking', 'adobe_tracking_param']):
        redirector_helper.insert_adgroup(ad_group.id, new_settings.get_tracking_codes(),
                                         new_settings.enable_ga_tracking,
                                         new_settings.enable_adobe_tracking,
                                         new_settings.adobe_tracking_param)

        if 'tracking_code' not in changes:
            changes['tracking_code'] = new_settings.get_tracking_codes()

    actions = []
    for field_name, field_value in changes.iteritems():
        if field_name in BLOCKED_AD_GROUP_SETTINGS:
            continue

        ad_group_sources = ad_group.adgroupsource_set.all()
        for ad_group_source in ad_group_sources:
            # if source supports setting action do an automatic update,
            # otherwise do manual actiontype
            source = ad_group_source.source
            if source.deprecated:
                logger.info(
                    'Skipping create action for property set %s for deprecated source %d',
                    field_name,
                    source.id
                )
                continue

            new_field_value = field_value
            force_manual_change = False
            if field_name == 'tracking_code':
                new_field_value = utils.url_helper.combine_tracking_codes(
                    new_settings.get_tracking_codes(),
                    ad_group_source.get_tracking_ids() if new_settings.enable_ga_tracking else ''
                )

                # Temporary bug fix for a bug in Gravity - codes that don't have a value assigned can not
                # be assigned automatically
                if new_field_value and any(('=' not in tc) for tc in new_field_value.split('&')) and\
                   ad_group_source.source.source_type.type == constants.SourceType.GRAVITY:
                    force_manual_change = True

            if field_name == 'ad_group_name':
                new_field_value = ad_group_source.get_external_name(new_adgroup_name=field_value)

            did_dmas_change = False
            did_countries_change = False
            if field_name == 'target_regions':
                did_dmas_change = new_settings.targets_dma() or current_settings.targets_dma()
                did_countries_change = new_settings.targets_countries() or current_settings.targets_countries()

            if (field_name == 'start_date' and source.can_modify_start_date() or
               field_name == 'end_date' and source.can_modify_end_date() or
               field_name == 'target_devices' and source.can_modify_device_targeting() or
               (field_name == 'tracking_code' and source.can_modify_tracking_codes() and not
                source.update_tracking_codes_on_content_ads()) or
               field_name == 'iab_category' and source.can_modify_ad_group_iab_category_automatic() or
               field_name == 'ad_group_name' and source.can_modify_ad_group_name() or
               field_name == 'target_regions' and can_modify_selected_target_regions_automatically(
                   source, did_countries_change, did_dmas_change)) and not force_manual_change:
                new_field_name = field_name
                if field_name == 'ad_group_name':
                    new_field_name = 'name'

                actions.extend(
                    actionlog.api.set_ad_group_source_settings(
                        {new_field_name: new_field_value},
                        ad_group_source,
                        request,
                        order,
                        send=send
                    )
                )

            elif field_name == 'tracking_code' and source.update_tracking_codes_on_content_ads() and source.can_modify_tracking_codes():
                if not ad_group_source.can_manage_content_ads:
                    continue

                for cas in models.ContentAdSource.objects.filter(
                        content_ad__ad_group_id=ad_group_source.ad_group_id,
                        source_id=ad_group_source.source_id
                ).select_related('content_ad'):
                    changes = {
                        'url': cas.content_ad.url_with_tracking_codes(new_field_value),
                    }

                    actions.append(
                        actionlog.api_contentads.init_update_content_ad_action(
                            cas,
                            changes,
                            request,
                            send=send
                        )
                    )
            else:
                if field_name in ['enable_ga_tracking', 'enable_adobe_tracking', 'adobe_tracking_param']:
                    # do not create an action - only used for our redirector
                    continue

                if field_name == 'iab_category' and not source.can_modify_ad_group_iab_category_manual():
                    continue

                if field_name == 'tracking_code':
                    tracking_slug = ad_group_source.source.tracking_slug
                    new_field_value = _substitute_tracking_macros(new_field_value, tracking_slug)

                if field_name == 'target_regions':
                    if not can_modify_selected_target_regions_manually(source, did_countries_change, did_dmas_change):
                        continue

                    new_field_value = _get_manual_action_target_regions_value(
                        ad_group_source,
                        new_field_value,
                        did_countries_change,
                        did_dmas_change,
                    )

                actionlog.api.init_set_ad_group_manual_property(
                    ad_group_source,
                    request,
                    field_name,
                    new_field_value
                )

    return actions


def create_global_publisher_blacklist_actions(ad_group, request, state, publisher_blacklist, send=True):
    if publisher_blacklist == []:
        return []

    blacklisted_publishers = {}
    # separate publishers per source type
    source_type_cache = {}
    blacklist_per_source = {}
    for publisher in publishers:
        source = publisher['source']
        source_type_id = source.source_type.id
        source_type_cache[source_type_id] = source.source_type
        blacklist_per_source[source_type_id] =\
            blacklist_per_source.get(source_type_id, [])
        blacklist_per_source[source_type_id].append(publisher)

    # send actions
    for source_type_id, blacklist in blacklist_per_source.iteritems():
        filtered_blacklist = [publisher for publisher in blacklist\
                              if publisher['source'].can_modify_publisher_blacklist_automatically()]
        # we only support per account outbrain blacklist
        if source_type_id == constants.SourceType.OUTBRAIN:
            continue
        if filtered_blacklist == []:
            continue

        key = None
        level = constants.PublisherBlacklistLevel.GLOBAL

        blacklisted_publishers[source_type_id].extend(
            list(map(lambda pub: {
                'domain': pub['domain'],
            }, filtered_blacklist))
        )

        actions.extend(
            actionlog.api.set_publisher_blacklist(
                key,
                level,
                state,
                blacklisted_publishers,
                request,
                source_type_cache[source_type_id],
                send=send
            )
        )

    return actions


def create_publisher_blacklist_actions(ad_group, state, level, publishers, request, send=True):
    if level == constants.PublisherBlacklistLevel.GLOBAL:
        return []
    if publishers == []:
        return []

    actions = []

    blacklisted_publishers = {}

    source_type_cache = {}
    blacklist_per_source = {}
    for publisher in publishers:
        source = publisher['source']
        source_type_id = source.source_type.id
        source_type_cache[source_type_id] = source.source_type
        blacklist_per_source[source_type_id] =\
            blacklist_per_source.get(source_type_id, [])
        blacklist_per_source[source_type_id].append(publisher)

    # send actions
    for source_type_id, blacklist in blacklist_per_source.iteritems():
        filtered_blacklist = [publisher for publisher in blacklist\
                              if publisher['source'].can_modify_publisher_blacklist_automatically()]
        # we only support per account outbrain blacklist
        if source_type_id == constants.SourceType.OUTBRAIN and\
                level != constants.PublisherBlacklistLevel.ACCOUNT:
            continue
        if filtered_blacklist == []:
            continue

        blacklisted_publishers[source_type_id] =\
            blacklisted_publishers.get(source_type_id, [])

        blacklisted_publishers[source_type_id].extend(
            list(map(lambda pub: {
                'domain': pub['domain'],
                'exchange': pub['source'].tracking_slug.replace('b1_', ''),
            }, filtered_blacklist))
        )

    if blacklisted_publishers != {}:
        for source_type_id, blacklist in blacklisted_publishers.iteritems():
            key = None
            if level == constants.PublisherBlacklistLevel.ACCOUNT:
                key = [ad_group.campaign.account.id]
                if source_type_id == constants.SourceType.OUTBRAIN:
                    key.append(ad_group.campaign.account.outbrain_marketer_id)
            elif level == constants.PublisherBlacklistLevel.CAMPAIGN:
                key = [ad_group.campaign.id]
            elif level == constants.PublisherBlacklistLevel.ADGROUP:
                key = [ad_group.id]
            else:
                # should never occur
                raise Exception('Not implemented')

            actions.extend(
                actionlog.api.set_publisher_blacklist(
                    key,
                    level,
                    state,
                    blacklist,
                    request,
                    source_type_cache[source_type_id],
                    send=send
                )
            )
    return actions


def _get_manual_action_target_regions_value(ad_group_source, new_target_regions,
                                            did_countries_change, did_dmas_change):

    new_country_targeting = [tr for tr in new_target_regions if tr in regions.COUNTRY_BY_CODE]
    new_dma_targeting = [regions.DMA_BY_CODE[tr] for tr in new_target_regions if tr in regions.DMA_BY_CODE]

    if not new_country_targeting and not new_dma_targeting:
        new_country_targeting = 'cleared' if new_dma_targeting else 'Worldwide'

    new_field_value = {
        'countries': new_country_targeting
    }

    if did_dmas_change:
        if not new_dma_targeting:
            new_dma_targeting = 'cleared (no DMA targeting)'

        new_field_value['dma'] = new_dma_targeting

    return new_field_value


def _substitute_tracking_macros(tracking_code, tracking_slug):
    '''
    This code is duplicated in Z2 -- which will eventually become a problem.
    '''
    substitutions = {
        '{sourceDomain}': tracking_slug,
        '{sourceDomainUnderscore}': tracking_slug.replace('.', '_'),
    }

    suffix_tracking_code = tracking_code
    for substitution, value in substitutions.iteritems():
        suffix_tracking_code = suffix_tracking_code.replace(substitution, value)
    return suffix_tracking_code


def reconcile_articles(ad_group, raw_articles):
    if not ad_group:
        raise exc.ArticleReconciliationException('Missing ad group.')

    for raw_article in raw_articles:
        url, title = raw_article.get('url'), raw_article.get('title')
        if not title:
            raise exc.ArticleReconciliationException(
                'Missing article title. url={url}'.format(url=url)
            )
        if url is None:
            raise exc.ArticleReconciliationException(
                'Missing article url. title={title}'.format(title=title)
            )

        raw_article['url'] = utils.url_helper.clean_url(url)[0]

    articles = list(models.Article.objects.filter(ad_group=ad_group))

    url_title_article = {}
    for article in articles:
        url_title_article[(article.url, article.title)] = article

    reconciled_articles = []
    for raw_article in raw_articles:
        url, title = raw_article.get('url'), raw_article.get('title')
        article = url_title_article.get((url, title), None)
        if article is None:
            try:
                # transacton.atomic is necessary to roll back
                # the query in case IntegrityError happens.
                # See https://docs.djangoproject.com/en/1.7/topics/db/transactions/#controlling-transactions-explicitly
                with transaction.atomic():
                    article = models.Article.objects.create(ad_group=ad_group, url=url, title=title)
            except IntegrityError:
                logger.info(
                    u'Integrity error upon inserting article: title = {title}, url = {url}, ad group id = {ad_group_id}. '
                    u'Using existing article.'.
                    format(title=title, url=url, ad_group_id=ad_group.id)
                )
                article = models.Article.objects.get(ad_group=ad_group, url=url, title=title)
            url_title_article[(url, title)] = article
        reconciled_articles.append(article)

    return reconciled_articles


def get_state_by_account():
    qs = models.AdGroupSettings.objects.select_related('ad_group__campaign__account') \
        .distinct('ad_group_id').order_by('ad_group_id', '-created_dt') \
        .values('ad_group', 'ad_group__campaign__account', 'state')
    account_state = {}
    for row in qs:
        aid = row['ad_group__campaign__account']
        if aid not in account_state:
            account_state[aid] = set()
        account_state[aid].add(row['state'])

    def _acc_state(ag_states):
        if constants.AdGroupSettingsState.ACTIVE in ag_states:
            return constants.AdGroupSettingsState.ACTIVE
        return constants.AdGroupSettingsState.INACTIVE
    account_state = {aid: _acc_state(ag_states) for aid, ag_states in account_state.iteritems()}
    return account_state


def _update_content_ad_source_submission_status(content_ad_source, submission_status):
    if content_ad_source.source.source_type.type == constants.SourceType.OUTBRAIN and\
       content_ad_source.submission_status == constants.ContentAdSubmissionStatus.REJECTED and\
       submission_status == constants.ContentAdSubmissionStatus.PENDING:
        return False

    if content_ad_source.source.source_type.type == constants.SourceType.OUTBRAIN and\
       submission_status == constants.ContentAdSubmissionStatus.PENDING and\
       content_ad_source.content_ad.ad_group.campaign.account.outbrain_marketer_id == AUTOMATIC_APPROVAL_OUTBRAIN_ACCOUNT:
        content_ad_source.submission_status = constants.ContentAdSubmissionStatus.APPROVED
    else:
        content_ad_source.submission_status = submission_status

    return True


@newrelic.agent.function_trace()
def update_content_ads_state(content_ads, state, request):
    with transaction.atomic():
        models.ContentAd.objects.filter(id__in=[ca.id for ca in content_ads]).update(state=state)
        content_ad_sources = models.ContentAdSource.objects.filter(
            ~Q(state=state) | ~Q(source_state=state),
            content_ad_id__in=[ca.id for ca in content_ads],
        ).select_related('content_ad__ad_group', 'content_ad__batch', 'source')
        content_ad_sources.update(state=state)
        content_ad_sources = content_ad_sources.all()

        content_ad_sources_changes = []
        for content_ad_source in content_ad_sources:
            content_ad_sources_changes.append(
                (content_ad_source, {'state': content_ad_source.state})
            )

        actions = actionlog.api_contentads.init_bulk_update_content_ad_actions(
            content_ad_sources_changes,
            request
        )

    actionlog.zwei_actions.send(actions)


def add_content_ads_state_change_to_history(ad_group, content_ads, state, request):
    description = 'Content ad(s) {{ids}} set to {}.'.format(constants.ContentAdSourceState.get_text(state))

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    save_change_to_history(ad_group, description, request)


def add_content_ads_archived_change_to_history(ad_group, content_ads, archived, request):
    description = 'Content ad(s) {{ids}} {}.'.format('Archived' if archived else 'Restored')

    description = format_bulk_ids_into_description([ad.id for ad in content_ads], description)

    save_change_to_history(ad_group, description, request)


def save_change_to_history(ad_group, description, request):
    settings = ad_group.get_current_settings().copy_settings()
    settings.changes_text = description
    settings.save(request)


def format_bulk_ids_into_description(ids, description_template):
    num_id_limit = 10

    shorten = len(ids) > num_id_limit

    ids_text = '{}{}'.format(', '.join(map(str, ids[:num_id_limit])),
                             ' and {} more'.format(len(ids) - num_id_limit) if shorten else '')

    return description_template.format(ids=ids_text)


class AdGroupSourceSettingsWriter(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def set(self, settings_obj, request, send_action=True):
        latest_settings = self.get_latest_settings()

        state = settings_obj.get('state')
        cpc_cc = settings_obj.get('cpc_cc')
        daily_budget_cc = settings_obj.get('daily_budget_cc')
        autopilot_state = settings_obj.get('autopilot_state')

        assert cpc_cc is None or isinstance(cpc_cc, decimal.Decimal)
        assert daily_budget_cc is None or isinstance(daily_budget_cc, decimal.Decimal)

        if any([
                state is not None and state != latest_settings.state,
                autopilot_state is not None and autopilot_state != latest_settings.autopilot_state,
                cpc_cc is not None and cpc_cc != latest_settings.cpc_cc,
                daily_budget_cc is not None and daily_budget_cc != latest_settings.daily_budget_cc]):
            new_settings = latest_settings
            new_settings.pk = None  # make a copy of the latest settings

            old_settings_obj = {}

            if state is not None:
                new_settings.state = state
            if autopilot_state is not None:
                if new_settings.state == constants.AdGroupSettingsState.INACTIVE and\
                        autopilot_state == constants.AdGroupSourceSettingsAutopilotState.ACTIVE:
                    raise utils.exc.ValidationError('Auto-pilot can not be enabled when source is disabled.')
                old_settings_obj['autopilot_state'] = latest_settings.autopilot_state
                new_settings.autopilot_state = autopilot_state
            if cpc_cc is not None:
                old_settings_obj['cpc_cc'] = latest_settings.cpc_cc
                new_settings.cpc_cc = cpc_cc
            if daily_budget_cc is not None:
                old_settings_obj['daily_budget_cc'] = latest_settings.daily_budget_cc
                new_settings.daily_budget_cc = daily_budget_cc
            new_settings.save(request)

            self.add_to_history(settings_obj, old_settings_obj, request)

            if request:
                email_helper.send_ad_group_notification_email(self.ad_group_source.ad_group, request)

            if send_action:
                filtered_settings_obj = {k: v for k, v in settings_obj.iteritems() if k != 'autopilot_state'}
                if 'state' not in settings_obj or self.can_trigger_action():
                    if filtered_settings_obj:
                        actionlog.api.set_ad_group_source_settings(filtered_settings_obj, new_settings.ad_group_source, request)
                else:
                    logger.info(
                        'settings=%s on ad_group_source=%s will be triggered when the ad group will be enabled',
                        settings_obj,
                        self.ad_group_source
                    )
        elif send_action:
            ssc = consistency.SettingsStateConsistence(self.ad_group_source)
            if not ssc.is_consistent() and ('state' not in settings_obj or self.can_trigger_action()):
                new_settings = latest_settings
                new_settings.pk = None  # make a copy of the latest settings
                new_settings.save(request)
                logger.info(
                    'settings for ad_group_source=%s did not change, but state is inconsistent, triggering actions',
                    self.ad_group_source
                )
                actionlog.api.set_ad_group_source_settings(settings_obj, latest_settings.ad_group_source, request)

    def can_trigger_action(self):
        try:
            ad_group_settings = models.AdGroupSettings.objects \
                .filter(ad_group=self.ad_group_source.ad_group) \
                .latest('created_dt')
            return ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE
        except models.AdGroupSettings.DoesNotExist:
            return False

    def get_latest_settings(self):
        try:
            latest_settings = models.AdGroupSourceSettings.objects \
                .filter(ad_group_source=self.ad_group_source) \
                .latest('created_dt')
            return latest_settings
        except models.AdGroupSourceSettings.DoesNotExist:
            return models.AdGroupSourceSettings(ad_group_source=self.ad_group_source)

    def add_to_history(self, change_obj, old_change_obj, request):
        changes_text_parts = []
        for key, val in change_obj.items():
            if val is None:
                continue

            field = models.AdGroupSettings.get_human_prop_name(key)
            val = models.AdGroupSettings.get_human_value(key, val)
            source_name = self.ad_group_source.source.name

            old_val = old_change_obj.get(key)

            if old_val is None:
                text = '%s %s set to %s' % (source_name, field, val)
            else:
                old_val = models.AdGroupSettings.get_human_value(key, old_val)
                text = '%s %s set from %s to %s' % (source_name, field, old_val, val)

            changes_text_parts.append(text)

        changes_text = ', '.join(changes_text_parts)

        settings = self.ad_group_source.ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)


def get_content_ad(content_ad_id):
    try:
        return models.ContentAd.objects.get(pk=content_ad_id)
    except models.ContentAd.DoesNotExist:
        return None


def can_modify_selected_target_regions_automatically(source, did_countries_change, did_dmas_change):
    modify_country_auto = source.can_modify_country_targeting()
    modify_dma_auto = source.can_modify_dma_targeting_automatic()
    return any([
        (modify_dma_auto and modify_country_auto),
        (modify_dma_auto and not did_countries_change),
        (modify_country_auto and not did_dmas_change)
    ])


def can_modify_selected_target_regions_manually(source, did_countries_change, did_dmas_change):
    return ((did_dmas_change and source.can_modify_dma_targeting_manual()) or
            (did_countries_change and not source.can_modify_country_targeting()))
