from collections import defaultdict
import datetime
import decimal
import logging
import newrelic.agent

from django.db import transaction, IntegrityError
from django.db.models import Q

import dash.models
import utils.exc
from utils import redirector_helper
from utils import email_helper
from utils import k1_helper
from utils import converters

from dash import exc
from dash import models
from dash import constants
from dash import consistency
from dash import region_targeting_helper
from dash import publisher_helpers

import utils.url_helper

logger = logging.getLogger(__name__)


# State of an ad group is set automatically.
# For changes of cpc_cc and daily_budget_cc, mail is sufficient
# There should be no manual actions for
# display_url, brand_name, description and call_to_action
BLOCKED_AD_GROUP_SETTINGS = [
    'state', 'cpc_cc', 'max_cpm', 'daily_budget_cc', 'display_url',
    'brand_name', 'description', 'call_to_action',
    'autopilot_state', 'autopilot_daily_budget', 'landing_mode',
    'b1_sources_group_enabled', 'b1_sources_group_daily_budget'
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


@transaction.atomic()
def update_content_ads_submission_status(ad_group_source, request=None):
    models.ContentAdSource.objects.filter(
        content_ad__ad_group_id=ad_group_source.ad_group_id,
        source_id=ad_group_source.source_id,
        submission_status__in=[constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                               constants.ContentAdSubmissionStatus.PENDING]
    ).update(
        source_content_ad_id=ad_group_source.source_content_ad_id,
        submission_status=ad_group_source.submission_status,
    )


def update_ad_group_redirector_settings(ad_group, ad_group_settings):
    campaign_settings = ad_group.campaign.get_current_settings()
    redirector_helper.insert_adgroup(
        ad_group,
        ad_group_settings,
        campaign_settings,
    )


def order_ad_group_settings_update(ad_group, current_settings, new_settings, request, send=True, iab_update=False,
                                   campaign_tracking_changes=False):
    changes = current_settings.get_setting_changes(new_settings)

    campaign_settings = ad_group.campaign.get_current_settings()
    # TODO: temporary hack to prevent changing IAB category every time settings
    # update is called - this should be moved to adgroup settings
    if iab_update:
        changes['iab_category'] = campaign_settings.iab_category

    has_tracking_changes = 'tracking_code' in changes or campaign_tracking_changes

    # insert settings into redirector if settings are fresh or if there are some changes
    # this way the ad groups settings are kept consistent between external sources, z1 and
    # redirector
    if current_settings.id is None or has_tracking_changes:
        update_ad_group_redirector_settings(ad_group, new_settings)

    # add tracking_code key if any change in tracking settings, so that the tracking codes
    # get recalculated and propagated to external sources
    if has_tracking_changes and 'tracking_code' not in changes:
        changes['tracking_code'] = new_settings.get_tracking_codes()

    if not changes:
        return []

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
                    ad_group_source.get_tracking_ids() if campaign_settings.enable_ga_tracking else ''
                )

                # Temporary bug fix for a bug in Gravity - codes that don't have a value assigned can not
                # be assigned automatically
                if new_field_value and any(('=' not in tc) for tc in new_field_value.split('&')) and\
                   ad_group_source.source.source_type.type == constants.SourceType.GRAVITY:
                    force_manual_change = True

            if field_name == 'ad_group_name':
                new_field_value = ad_group_source.get_external_name(new_adgroup_name=field_value)

            if is_adg_setting_auto_updateable(
                field_name, source, current_settings, new_settings
            ) and not force_manual_change:
                pass
            elif field_name == 'tracking_code' and source.update_tracking_codes_on_content_ads():
                pass
            else:
                adg_setting_manual_update(
                    request,
                    ad_group_source,
                    field_name,
                    new_field_value,
                    current_settings,
                    new_settings
                )


def is_adg_setting_auto_updateable(field_name, source, current_settings, new_settings):
    setting_updateable = (
        field_name == 'start_date' and source.can_modify_start_date(),
        field_name == 'end_date' and source.can_modify_end_date(),
        field_name == 'target_devices' and source.can_modify_device_targeting(),
        field_name == 'tracking_code' and not source.update_tracking_codes_on_content_ads(),
        field_name == 'iab_category' and source.can_modify_ad_group_iab_category_automatic(),
        field_name == 'ad_group_name' and source.can_modify_ad_group_name(),
        field_name == 'retargeting_ad_groups' and source.can_modify_retargeting_automatically(),
        field_name == 'exclusion_retargeting_ad_groups' and source.can_modify_retargeting_automatically(),
        field_name == 'audience_targeting' and source.can_modify_retargeting_automatically(),
        field_name == 'exclusion_audience_targeting' and source.can_modify_retargeting_automatically(),
        field_name == 'target_regions' and region_targeting_helper.can_modify_selected_target_regions_automatically(
            source,
            current_settings,
            new_settings
        ),
    )
    return any(setting_updateable)


def adg_setting_manual_update(
    request,
    ad_group_source,
    field_name,
    field_value,
    current_settings,
    new_settings
):
    source = ad_group_source.source

    if field_name in [
            'enable_ga_tracking',
            'enable_adobe_tracking',
            'adobe_tracking_param',
            'ga_tracking_type',
            'ga_property_id']:
        # do not create an action - only used for our redirector
        return

    if field_name in [
            'retargeting_ad_groups',
            'exclusion_retargeting_ad_groups',
            'audience_targeting',
            'exclusion_audience_targeting'] and not source.can_modify_retargeting_manually():
        return

    if field_name == 'iab_category' and not source.can_modify_ad_group_iab_category_manual():
        return

    if field_name == 'tracking_code':
        tracking_slug = ad_group_source.source.tracking_slug
        field_value = _substitute_tracking_macros(field_value, tracking_slug)

    if field_name == 'target_regions':
        if not region_targeting_helper.can_modify_selected_target_regions_manually(source, current_settings, new_settings):
            return

        field_value = _get_manual_action_target_regions_value(
            ad_group_source,
            current_settings,
            new_settings
        )


def _create_blacklist_per_source(publishers):
    source_type_cache = {}
    blacklist_per_source = {}
    for publisher in publishers:
        source = publisher['source']
        source_type_id = source.source_type.id
        source_type_cache[source_type_id] = source.source_type
        blacklist_per_source[source_type_id] =\
            blacklist_per_source.get(source_type_id, [])
        blacklist_per_source[source_type_id].append(publisher)

    return blacklist_per_source, source_type_cache


def _get_manual_action_target_regions_value(ad_group_source, current_settings, new_settings):
    new_country_targeting = new_settings.get_targets_for_region_type(constants.RegionType.COUNTRY)
    new_subdivision_targeting = new_settings.get_target_names_for_region_type(constants.RegionType.SUBDIVISION)
    new_dma_targeting = new_settings.get_target_names_for_region_type(constants.RegionType.DMA)

    # default to worldwide
    if not new_country_targeting and not new_subdivision_targeting and not new_dma_targeting:
        new_country_targeting = 'Worldwide'

    new_field_value = {
        'countries': new_country_targeting
    }

    if new_subdivision_targeting or\
       (current_settings is not None and current_settings.targets_region_type(constants.RegionType.SUBDIVISION)):
        if not new_subdivision_targeting:
            new_subdivision_targeting = 'cleared (no subdivision targeting)'

        new_field_value['subdivisions'] = new_subdivision_targeting

    if new_dma_targeting or\
       (current_settings is not None and current_settings.targets_region_type(constants.RegionType.DMA)):
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


class AdGroupSourceSettingsWriter(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def set(self, settings_obj, request, create_action=True, send_to_zwei=True, system_user=None, landing_mode=None):
        latest_settings = self.ad_group_source.get_current_settings()

        state = settings_obj.get('state')
        cpc_cc = settings_obj.get('cpc_cc')
        daily_budget_cc = settings_obj.get('daily_budget_cc')

        assert cpc_cc is None or isinstance(cpc_cc, decimal.Decimal)
        assert daily_budget_cc is None or isinstance(daily_budget_cc, decimal.Decimal)

        if any([
                state is not None and state != latest_settings.state,
                cpc_cc is not None and cpc_cc != latest_settings.cpc_cc,
                daily_budget_cc is not None and daily_budget_cc != latest_settings.daily_budget_cc,
                landing_mode is not None and landing_mode != latest_settings.landing_mode
        ]):
            new_settings = self.update_settings(
                request,
                latest_settings,
                settings_obj,
                state,
                cpc_cc,
                daily_budget_cc,
                landing_mode,
                system_user=system_user
            )
            self.create_action_on_settings_change(
                request,
                create_action,
                settings_obj,
                new_settings,
                send_to_zwei=send_to_zwei
            )
        else:
            self.create_action_on_no_change(
                request,
                create_action,
                settings_obj,
                latest_settings,
                send_to_zwei=send_to_zwei
            )
        return []

    def update_settings(self,
                        request,
                        latest_settings,
                        settings_obj,
                        state,
                        cpc_cc,
                        daily_budget_cc,
                        landing_mode,
                        system_user=None):
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
        self.notify(settings_obj, old_settings_obj, request, system_user)
        return new_settings

    def create_action_on_settings_change(self, request, create_action, settings_obj, new_settings, send_to_zwei=True):
        if not create_action:
            return
        filtered_settings_obj = {k: v for k, v in settings_obj.iteritems()}
        if 'state' not in settings_obj or self.can_trigger_action():
            if filtered_settings_obj:
                if send_to_zwei:
                    k1_helper.update_ad_group(self.ad_group_source.ad_group_id, msg='AdGroupSourceSettingsWriter')
        else:
            logger.info(
                'settings=%s on ad_group_source=%s will be triggered when the ad group will be enabled',
                settings_obj,
                self.ad_group_source
            )

    def create_action_on_no_change(self, request, create_action, settings_obj, latest_settings, send_to_zwei=True):
        if not create_action:
            return

        ssc = consistency.SettingsStateConsistence(self.ad_group_source)
        if not ssc.is_consistent() and ('state' not in settings_obj or self.can_trigger_action()):
            new_settings = latest_settings
            new_settings.pk = None  # make a copy of the latest settings
            new_settings.save(request, action_type=constants.HistoryActionType.MEDIA_SOURCE_SETTINGS_CHANGE)
            logger.info(
                'settings for ad_group_source=%s did not change, but state is inconsistent, triggering actions',
                self.ad_group_source
            )
            if send_to_zwei:
                k1_helper.update_ad_group(self.ad_group_source.ad_group_id, msg='AdGroupSourceSettingsWriter')

    def can_trigger_action(self):
        ad_group_settings = self.ad_group_source.ad_group.get_current_settings()
        return models.AdGroup.is_ad_group_active(ad_group_settings)

    def notify(self, change_obj, old_change_obj, request, system_user):
        if not request:
            return

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

        email_helper.send_ad_group_notification_email(
            self.ad_group_source.ad_group, request, '\n'.join(changes_text_parts))


def get_content_ad(content_ad_id):
    try:
        return models.ContentAd.objects.get(pk=content_ad_id)
    except models.ContentAd.DoesNotExist:
        return None
