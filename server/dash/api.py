import decimal
import json
import logging

from django.db import transaction, IntegrityError

import actionlog.api
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
def update_ad_group_source_state(ad_group_source, conf, settings_id=None):
    for key, val in conf.items():
        if key in ('cpc_cc', 'daily_budget_cc'):
            conf[key] = cc_to_decimal(val)

    if settings_id is None:
        _upsert_ad_group_source_state(ad_group_source, conf)
        return
    try:
        latest_ad_group_source_settings = models.AdGroupSourceSettings.objects\
            .filter(ad_group_source=ad_group_source) \
            .latest('created_dt')
    except models.AdGroupSourceSettings.DoesNotExist:
        logger.warning('no ad_group_source_settings found')
        latest_ad_group_source_settings = None

    if latest_ad_group_source_settings is None or latest_ad_group_source_settings.id == settings_id:
        # we are updating for the latest settings
        # or no settings are specified
        # we have to update the state
        _upsert_ad_group_source_state(ad_group_source, conf)
        return

    assert latest_ad_group_source_settings.id != settings_id
    # we don't do any update for an ad_group_source_settings which isn't the most recent


def _upsert_ad_group_source_state(ad_group_source, conf):
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


def update_campaign_key(ad_group_source, source_campaign_key):
    ad_group_source.source_campaign_key = json.dumps(source_campaign_key)
    ad_group_source.save()


def order_ad_group_settings_update(ad_group, current_settings, new_settings):
    changes = current_settings.get_setting_changes(new_settings)

    if not changes:
        return

    for field_name, field_value in changes.iteritems():
        if field_name == 'state' and field_value == constants.AdGroupSettingsState.INACTIVE:
            actionlog.api.init_stop_ad_group_order(ad_group)
        else:
            actionlog.api.init_set_ad_group_property_order(ad_group, prop=field_name, value=field_value)


def reconcile_article(raw_url, title, ad_group):
    if not ad_group:
        raise exc.ArticleReconciliationException('Missing ad group.')

    if not title:
        raise exc.ArticleReconciliationException('Missing article title. url={url}'.format(url=raw_url))

    if raw_url is None:
        raise exc.ArticleReconciliationException('Missing article url. title={title}'.format(title=title))

    url, _ = clean_url(raw_url)

    try:
        return models.Article.objects.get(ad_group=ad_group, title=title, url=url)
    except models.Article.DoesNotExist:
        pass

    try:
        with transaction.atomic():
            return models.Article.objects.create(ad_group=ad_group, url=url, title=title)
    except IntegrityError:
        logger.info(
            u'Integrity error upon inserting article: title = {title}, url = {url}, ad group id = {ad_group_id}. '
            u'Using existing article.'.
            format(title=title, url=url, ad_group_id=ad_group.id)
        )
        return models.Article.objects.get(ad_group=ad_group, url=url, title=title)


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

    def set(self, settings_obj):
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
                new_settings.save()

                self.add_to_history(settings_obj, old_settings_obj)

                if self.can_trigger_action():
                    actionlog.api.set_ad_group_source_settings(settings_obj, new_settings)
                else:
                    logger.info(
                        'settings=%s on ad_group_source=%s will be triggered when the ad group will be enabled',
                        settings_obj,
                        self.ad_group_source
                    )
        else:
            ssc = consistency.SettingsStateConsistence(self.ad_group_source)
            if not ssc.is_consistent() and self.can_trigger_action():
                new_settings = latest_settings
                new_settings.pk = None  # make a copy of the latest settings
                new_settings.save()
                logger.info(
                    'settings for ad_group_source=%s did not change, but state is inconsistent, triggering actions',
                    self.ad_group_source
                )
                actionlog.api.set_ad_group_source_settings(settings_obj, latest_settings)

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

    def add_to_history(self, change_obj, old_change_obj):
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
        new_ad_group_settings.save()
