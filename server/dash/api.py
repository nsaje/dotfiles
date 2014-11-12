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
from utils.url import clean_url

logger = logging.getLogger(__name__)


def cc_to_decimal(val_cc):
    if val_cc is None:
        return None
    return decimal.Decimal(val_cc) / 10000


# @transaction.atomic
# def campaign_status_upsert(ad_group_source, data):
#     '''
#     Creates new AdGroupSourceSettings if settings are modified.
#     '''

#     new_settings = {
#         'state': data.get('state'),
#         'cpc_cc': cc_to_decimal(data.get('cpc_cc')),
#         'daily_budget_cc': cc_to_decimal(data.get('daily_budget_cc')),
#     }

#     try:
#         current_settings = ad_group_source.settings.latest()
#     except models.AdGroupSourceSettings.DoesNotExist:
#         current_settings = None

#     if current_settings is not None and (
#         current_settings.state == new_settings['state'] and
#         current_settings.cpc_cc == new_settings['cpc_cc'] and
#         current_settings.daily_budget_cc == new_settings['daily_budget_cc']
#     ):
#         logger.info('Campaign settings for ad_group_source %s unmodified', ad_group_source)
#         return

#     ad_group_source.settings.create(**new_settings)


# @transaction.atomic
# def update_campaign_state(ad_group_source, state):
#     '''
#     Creates new AdGroupSourceSettings if settings are modified.
#     '''
#     try:
#         current_settings = ad_group_source.settings.latest()
#     except models.AdGroupSourceSettings.DoesNotExist:
#         current_settings = None

#     if current_settings is not None:
#         if state == current_settings.state:
#             logger.info('Campaign settings for ad_group_source %s unmodified', ad_group_source)
#             return
#         else:
#             current_settings.pk = None  # create a new settings object as a copy of the old one
#             current_settings.state = state
#             current_settings.save()


@transaction.atomic
def update_ad_group_source_state(ad_group_source, conf, settings_id=None):
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
        return 
        ## TODO:
        # below is the "real" code :)
        if ad_group_source_state is None:
            new_state = models.AdGroupSourceState.create(ad_group_source=ad_group_source)
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
    # TODO:
    # stub
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
