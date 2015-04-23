import decimal
import logging

from django.db import transaction, IntegrityError
from django.db.models import Q

import actionlog.api
import actionlog.api_contentads
import actionlog.models
import actionlog.constants

from dash import exc
from dash import models
from dash import constants
from dash import consistency
from utils.url import clean_url

logger = logging.getLogger(__name__)


def cc_to_decimal(val_cc):
    if val_cc is None:
        return None
    return decimal.Decimal(val_cc) / 10000


@transaction.atomic
def add_content_ad_sources(ad_group_source, request=None):
    if not ad_group_source.source.can_manage_content_ads():
        return

    content_ads = models.ContentAd.objects.filter(ad_group=ad_group_source.ad_group)

    for content_ad in content_ads:
        try:
            content_ad_source = models.ContentAdSource.objects.get(content_ad=content_ad, source=ad_group_source.source)
        except models.ContentAdSource.DoesNotExist:
            content_ad_source = models.ContentAdSource.objects.create(
                source=ad_group_source.source,
                content_ad=content_ad,
                submission_status=constants.ContentAdSubmissionStatus.PENDING,
                state=constants.ContentAdSourceState.ACTIVE
            )

        actionlog.api_contentads.init_insert_content_ad_action(content_ad_source, request)


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
                    key == 'cpc_cc' and  ad_group_source_state.cpc_cc != val,
                    key == 'daily_budget_cc' and  ad_group_source_state.daily_budget_cc != val,
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
        new_state.save()


def _get_latest_ad_group_source_state(ad_group_source):
    try:
        agss = models.AdGroupSourceState.objects.filter(ad_group_source=ad_group_source).latest()
        return agss
    except models.AdGroupSourceState.DoesNotExist:
        return None


def update_campaign_key(ad_group_source, source_campaign_key, request):
    ad_group_source.source_campaign_key = source_campaign_key
    ad_group_source.save(request)


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
        content_ad_source.submission_status = submission_status
        content_ad_source.submission_errors = submission_errors

    content_ad_source.save()


def submit_ad_group_callback(ad_group_source, source_content_ad_id, submission_status, submission_errors):
    if ad_group_source.source.content_ad_submission_type != constants.SourceSubmissionType.AD_GROUP:
        raise Exception('Invalid source submission type')

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
            content_ad_source.submission_errors = submission_errors
            content_ad_source.save()

    for content_ad_source in content_ad_sources:
        actionlog.api_contentads.init_insert_content_ad_action(content_ad_source, request=None)


def submit_content_ads_batch(ad_group_id, batch, request):
    ad_groups_to_submit = []
    content_ads_to_send = []
    with transaction.atomic():
        for ad_group_source in models.AdGroupSource.objects.filter(ad_group_id=ad_group_id):
            content_ad_sources = list(
                models.ContentAdSource.objects.filter(
                    Q(source_content_ad_id__isnull=True) | Q(source_content_ad_id=''),
                    content_ad__ad_group_id=ad_group_id,
                    source=ad_group_source.source,
                    content_ad__batch=batch,
                    submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                )
            )

            if not content_ad_sources:
                continue

            if ad_group_source.source.content_ad_submission_type == constants.SourceSubmissionType.AD_GROUP:
                if actionlog.models.ActionLog.objects.filter(
                        ad_group_source=ad_group_source,
                        action=actionlog.constants.Action.SUBMIT_AD_GROUP,
                        state=actionlog.constants.ActionState.WAITING,
                ).exists():
                    continue

                if ad_group_source.submission_status == constants.ContentAdSubmissionStatus.NOT_SUBMITTED:
                    ad_groups_to_submit.append((ad_group_source, content_ad_sources[0]))
                    continue

                if ad_group_source.submission_status != constants.ContentAdSubmissionStatus.PENDING and\
                   ad_group_source.submission_status != constants.ContentAdSubmissionStatus.APPROVED and\
                   ad_group_source.submission_status != constants.ContentAdSubmissionStatus.REJECTED:
                    continue

                for content_ad_source in content_ad_sources:
                    content_ad_source.source_content_ad_id = ad_group_source.source_content_ad_id
                    content_ad_source.submission_status = ad_group_source.submission_status
                    content_ad_source.submission_errors = ad_group_source.submission_errors
                    content_ad_source.save()

            content_ads_to_send.extend(content_ad_sources)

    for ad_group_source, content_ad_source in ad_groups_to_submit:
        actionlog.api_contentads.init_submit_ad_group_action(
            ad_group_source,
            content_ad_source,
            request
        )

    for content_ad_source in content_ads_to_send:
        actionlog.api_contentads.init_insert_content_ad_action(content_ad_source, request)


@transaction.atomic()
def update_multiple_content_ad_source_states(ad_group_source, content_ad_data):
    content_ad_sources = {}

    for content_ad_source in models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group_source.ad_group,
            source=ad_group_source.source):
        content_ad_sources[content_ad_source.get_source_id()] = content_ad_source

    for data in content_ad_data:
        content_ad_source = content_ad_sources.get(data['id'])

        if content_ad_source is None:
            continue

        changed = False

        if data['state'] != content_ad_source.source_state:
            content_ad_source.source_state = data['state']
            changed = True

        if 'submission_status' in data and data['submission_status'] != content_ad_source.submission_status:
            content_ad_source.submission_status = data['submission_status']
            changed = True

        if changed:
            content_ad_source.save()


def update_content_ad_source_state(content_ad_source, data):
    state = data['source_state']
    submission_status = data['submission_status']

    if state:
        content_ad_source.source_state = state

    if submission_status:
        content_ad_source.submission_status = submission_status

    content_ad_source.save()


def order_ad_group_settings_update(ad_group, current_settings, new_settings, request):
    changes = current_settings.get_setting_changes(new_settings)

    campaign_settings = ad_group.campaign.get_current_settings()
    changes['iab_category'] = campaign_settings.iab_category

    if not changes:
        return

    order = actionlog.models.ActionLogOrder.objects.create(
        order_type=actionlog.constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
    )

    for field_name, field_value in changes.iteritems():
        # State of an ad group is set automatically.
        # For changes of cpc_cc and daily_budget_cc, mail is sufficient
        # There should be no manual actions for
        # display_url, brand_name, description and call_to_action
        if field_name in ['state', 'cpc_cc', 'daily_budget_cc', 'display_url',
                          'brand_name', 'description', 'call_to_action']:
            continue

        ad_group_sources = ad_group.adgroupsource_set.all()
        for ad_group_source in ad_group_sources:
            # if source supports setting action do an automatic update,
            # otherwise do manual actiontype
            source = ad_group_source.source
            if field_name == 'start_date' and source.can_modify_start_date() or\
                field_name == 'end_date' and source.can_modify_end_date() or\
                field_name in ('target_devices', 'target_regions') and source.can_modify_targeting() or\
                field_name == 'tracking_code' and source.can_modify_tracking_codes() or\
                field_name == 'iab_category' and source.can_modify_ad_group_iab_category() or\
                field_name == 'ad_group_name' and source.can_modify_ad_group_name():

                if field_name == 'ad_group_name':
                    # adgroup name should have been changed by this point
                    field_name = 'name'
                    field_value = ad_group_source.get_external_name()

                actionlog.api.set_ad_group_source_settings({field_name: field_value}, ad_group_source, request, order)
            else:
                actionlog.api.init_set_ad_group_property_order(ad_group_source.ad_group, request, source=ad_group_source, prop=field_name, value=field_value)

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

        raw_article['url'] = clean_url(url)[0]

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
    account_state = {aid:_acc_state(ag_states) for aid, ag_states in account_state.iteritems()}
    return account_state


class AdGroupSourceSettingsWriter(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def set(self, settings_obj, request):
        latest_settings = self.get_latest_settings()

        state = settings_obj.get('state')
        cpc_cc = settings_obj.get('cpc_cc')
        daily_budget_cc = settings_obj.get('daily_budget_cc')

        assert cpc_cc is None or isinstance(cpc_cc, decimal.Decimal)
        assert daily_budget_cc is None or isinstance(daily_budget_cc, decimal.Decimal)

        if any([
                state is not None and state != latest_settings.state,
                cpc_cc is not None and cpc_cc != latest_settings.cpc_cc,
                daily_budget_cc is not None and daily_budget_cc != latest_settings.daily_budget_cc
        ]):
                new_settings = latest_settings
                new_settings.pk = None  # make a copy of the latest settings

                old_settings_obj = {}

                if state is not None:
                    new_settings.state = state
                if cpc_cc is not None:
                    old_settings_obj['cpc_cc'] = new_settings.cpc_cc
                    new_settings.cpc_cc = cpc_cc
                if daily_budget_cc is not None:
                    old_settings_obj['daily_budget_cc'] = new_settings.daily_budget_cc
                    new_settings.daily_budget_cc = daily_budget_cc
                new_settings.save(request)

                self.add_to_history(settings_obj, old_settings_obj, request)

                if 'state' not in settings_obj or self.can_trigger_action():
                    actionlog.api.set_ad_group_source_settings(settings_obj, new_settings.ad_group_source, request)
                else:
                    logger.info(
                        'settings=%s on ad_group_source=%s will be triggered when the ad group will be enabled',
                        settings_obj,
                        self.ad_group_source
                    )
        else:
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

        try:
            latest_ad_group_settings = models.AdGroupSettings.objects \
                .filter(ad_group=self.ad_group_source.ad_group) \
                .latest('created_dt')
        except models.AdGroupSettings.DoesNotExist:
            # there are no settings, we create the first one
            latest_ad_group_settings = models.AdGroupSettings(ad_group=self.ad_group_source.ad_group)

        new_ad_group_settings = latest_ad_group_settings
        new_ad_group_settings.pk = None
        new_ad_group_settings.changes_text = changes_text
        new_ad_group_settings.save(request)
