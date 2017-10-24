import influx
import datetime
import random
import string
import logging

from django.core.cache import caches
import dash.models

from etl import daily_statements_k1
from etl import materialize_views
from etl import maintenance

import utils.slack

logger = logging.getLogger(__name__)


AD_BREAKDOWN = ['date', 'source_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id']
AD_GROUP_BREAKDOWN = ['date', 'source_id', 'account_id', 'campaign_id', 'ad_group_id']
CAMPAIGN_BREAKDOWN = ['date', 'source_id', 'account_id', 'campaign_id']
ACCOUNT_BREAKDOWN = ['date', 'source_id', 'account_id']


MATERIALIZED_VIEWS = [
    # Views that help construct master view
    materialize_views.MVHelpersSource,
    materialize_views.MVHelpersAdGroupStructure,
    materialize_views.MVHelpersCampaignFactors,
    materialize_views.MVHelpersNormalizedStats,

    # Must be done before master, it is used there to generate empty rows for conversions
    materialize_views.MVTouchpointConversions,

    materialize_views.MasterView,
    materialize_views.MasterPublishersView,

    materialize_views.MVConversions,

    # VIEW: Ad Group, TAB: Ads
    materialize_views.MasterDerivedView.create(
        table_name='mv_contentad',
        breakdown=AD_BREAKDOWN,
        sortkey=AD_BREAKDOWN,
        distkey='content_ad_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_contentad_device',
        breakdown=AD_BREAKDOWN + ['device_type', 'device_os'],
        sortkey=AD_BREAKDOWN + ['device_type', 'device_os'],
        distkey='content_ad_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_contentad_placement',
        breakdown=AD_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        sortkey=AD_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        distkey='content_ad_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_contentad_geo',
        breakdown=AD_BREAKDOWN + ['country', 'state', 'dma'],
        sortkey=AD_BREAKDOWN + ['country', 'state', 'dma'],
        distkey='content_ad_id'),
    materialize_views.ConversionsDerivedView.create(
        table_name='mv_contentad_conv',
        breakdown=AD_BREAKDOWN + ['slug'],
        sortkey=AD_BREAKDOWN + ['slug'],
        distkey='content_ad_id'),
    materialize_views.TouchpointConversionsDerivedView.create(
        table_name='mv_contentad_touch',
        breakdown=AD_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        sortkey=AD_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        distkey='content_ad_id'),

    # VIEW: Ad Group, TAB: Sources
    # VIEW: Campaign, TAB: Ad Groups
    materialize_views.MasterDerivedView.create(
        table_name='mv_adgroup',
        breakdown=AD_GROUP_BREAKDOWN,
        sortkey=AD_GROUP_BREAKDOWN,
        distkey='ad_group_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_adgroup_device',
        breakdown=AD_GROUP_BREAKDOWN + ['device_type', 'device_os'],
        sortkey=AD_GROUP_BREAKDOWN + ['device_type', 'device_os'],
        distkey='ad_group_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_adgroup_placement',
        breakdown=AD_GROUP_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        sortkey=AD_GROUP_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        distkey='ad_group_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_adgroup_geo',
        breakdown=AD_GROUP_BREAKDOWN + ['country', 'state', 'dma'],
        sortkey=AD_GROUP_BREAKDOWN + ['country', 'state', 'dma'],
        distkey='ad_group_id'),
    materialize_views.ConversionsDerivedView.create(
        table_name='mv_adgroup_conv',
        breakdown=AD_GROUP_BREAKDOWN + ['slug'],
        sortkey=AD_GROUP_BREAKDOWN + ['slug'],
        distkey='ad_group_id'),
    materialize_views.TouchpointConversionsDerivedView.create(
        table_name='mv_adgroup_touch',
        breakdown=AD_GROUP_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        sortkey=AD_GROUP_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        distkey='ad_group_id'),

    # VIEW: Campaign, TAB: Sources
    # VIEW: Account, TAB: Campaigns
    materialize_views.MasterDerivedView.create(
        table_name='mv_campaign',
        breakdown=CAMPAIGN_BREAKDOWN,
        sortkey=CAMPAIGN_BREAKDOWN,
        distkey='campaign_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_campaign_device',
        breakdown=CAMPAIGN_BREAKDOWN + ['device_type', 'device_os'],
        sortkey=CAMPAIGN_BREAKDOWN + ['device_type', 'device_os'],
        distkey='campaign_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_campaign_placement',
        breakdown=CAMPAIGN_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        sortkey=CAMPAIGN_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        distkey='campaign_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_campaign_geo',
        breakdown=CAMPAIGN_BREAKDOWN + ['country', 'state', 'dma'],
        sortkey=CAMPAIGN_BREAKDOWN + ['country', 'state', 'dma'],
        distkey='campaign_id'),
    materialize_views.ConversionsDerivedView.create(
        table_name='mv_campaign_conv',
        breakdown=CAMPAIGN_BREAKDOWN + ['slug'],
        sortkey=CAMPAIGN_BREAKDOWN + ['slug'],
        distkey='campaign_id'),
    materialize_views.TouchpointConversionsDerivedView.create(
        table_name='mv_campaign_touch',
        breakdown=CAMPAIGN_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        sortkey=CAMPAIGN_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        distkey='campaign_id'),

    # VIEW: Account, TAB: Sources
    # VIEW: All Accounts, TAB: Accounts
    # VIEW: All Accounts, TAB: Sources
    materialize_views.MasterDerivedView.create(
        table_name='mv_account',
        breakdown=ACCOUNT_BREAKDOWN,
        sortkey=ACCOUNT_BREAKDOWN,
        distkey='account_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_account_device',
        breakdown=ACCOUNT_BREAKDOWN + ['device_type', 'device_os'],
        sortkey=ACCOUNT_BREAKDOWN + ['device_type', 'device_os'],
        distkey='account_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_account_placement',
        breakdown=ACCOUNT_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        sortkey=ACCOUNT_BREAKDOWN + ['placement_medium', 'placement_type', 'video_playback_method'],
        distkey='account_id'),
    materialize_views.MasterDerivedView.create(
        table_name='mv_account_geo',
        breakdown=ACCOUNT_BREAKDOWN + ['country', 'state', 'dma'],
        sortkey=ACCOUNT_BREAKDOWN + ['country', 'state', 'dma'],
        distkey='account_id'),
    materialize_views.ConversionsDerivedView.create(
        table_name='mv_account_conv',
        breakdown=ACCOUNT_BREAKDOWN + ['slug'],
        sortkey=ACCOUNT_BREAKDOWN + ['slug'],
        distkey='account_id'),
    materialize_views.TouchpointConversionsDerivedView.create(
        table_name='mv_account_touch',
        breakdown=ACCOUNT_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        sortkey=ACCOUNT_BREAKDOWN + ['slug', 'conversion_window', 'conversion_label'],
        distkey='account_id'),

    # View: Ad Group, Tab: Publishers
    materialize_views.MasterPublishersDerivedView.create(
        table_name='mv_adgroup_pubs',
        breakdown=AD_GROUP_BREAKDOWN + ['publisher', 'publisher_source_id', 'external_id'],
        sortkey=AD_GROUP_BREAKDOWN + ['publisher_source_id'],
        distkey='ad_group_id'),
    # View: Campaign, Tab: Publishers
    materialize_views.MasterPublishersDerivedView.create(
        table_name='mv_campaign_pubs',
        breakdown=CAMPAIGN_BREAKDOWN + ['publisher', 'publisher_source_id', 'external_id'],
        sortkey=CAMPAIGN_BREAKDOWN + ['publisher_source_id'],
        distkey='campaign_id'),
    # View: Account: Tab: Publishers
    # View: All Accounts: Tab: Publishers
    materialize_views.MasterPublishersDerivedView.create(
        table_name='mv_account_pubs',
        breakdown=ACCOUNT_BREAKDOWN + ['publisher', 'publisher_source_id', 'external_id'],
        sortkey=ACCOUNT_BREAKDOWN + ['publisher_source_id'],
        distkey='account_id'),
]


SLACK_MIN_DAYS_TO_PROCESS = 10


def _post_to_slack(status, update_since, account_id=None):
    utils.slack.publish('Materialization since {}{} *{}*.'.format(
        str(update_since.date()), account_id and ' for *account {}*'.format(account_id) or '', status
    ), msg_type=utils.slack.MESSAGE_TYPE_INFO, username='Refresh k1')


@influx.timer('etl.refresh_k1.refresh_k1_timer', type='all')
def refresh_k1_reports(update_since, account_id=None, skip_vacuum=False):
    do_post_to_slack = (datetime.datetime.today() - update_since).days > SLACK_MIN_DAYS_TO_PROCESS
    if do_post_to_slack:
        _post_to_slack('started', update_since, account_id)
    _refresh_k1_reports(update_since, MATERIALIZED_VIEWS, account_id, skip_vacuum=skip_vacuum)
    if do_post_to_slack:
        _post_to_slack('finished', update_since, account_id)


def _refresh_k1_reports(update_since, views, account_id=None, skip_vacuum=False):
    influx.incr('etl.refresh_k1.refresh_k1_reports', 1)

    if account_id:
        validate_can_reprocess_account(account_id)

    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date(), account_id)

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    job_id = generate_job_id(account_id)

    logger.info('Starting refresh k1 reports job %s for date range %s - %s, requested update since %s, %s',
                job_id, date_from, date_to, update_since, 'skip vacuum' if skip_vacuum else 'vacuum each table')

    extra_dayspan = (update_since.date() - date_from).days
    influx.gauge('etl.refresh_k1.extra_dayspan', extra_dayspan)
    if extra_dayspan:
        logger.warning(
            'Refresh K1 is processing older statements than requested (requested update since %s,'
            'real update since %s), job %s',
            update_since, date_from, job_id)

    for mv_class in views:
        mv = mv_class(job_id, date_from, date_to, account_id=account_id)
        with influx.block_timer('etl.refresh_k1.generate_table', table=mv_class.TABLE_NAME):
            mv.generate(campaign_factors=effective_spend_factors)

            try:
                if not skip_vacuum and not mv_class.IS_TEMPORARY_TABLE:
                    maintenance.vacuum(mv_class.TABLE_NAME)
                maintenance.analyze(mv_class.TABLE_NAME)
            except Exception:
                logger.exception("Vacuum and analyze skipped due to error")

    influx.incr('etl.refresh_k1.refresh_k1_reports_finished', 1)

    # while everything is being updated data is not consistent among tables
    # so might as well leave cache until refresh finishes
    invalidate_breakdowns_rs_cache()


def get_all_views_table_names(temporary=False):
    return [x.TABLE_NAME for x in MATERIALIZED_VIEWS if x.IS_TEMPORARY_TABLE is temporary]


def generate_job_id(account_id):
    epoch = datetime.datetime.utcfromtimestamp(0)
    timestamp = int((datetime.datetime.now() - epoch).total_seconds() * 1000)

    rnd_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

    if account_id:
        return "{}_A{}_{}".format(timestamp, account_id, rnd_str)

    return "{}_{}".format(timestamp, rnd_str)


def invalidate_breakdowns_rs_cache():
    cache = caches['breakdowns_rs']
    cache.clear()


def validate_can_reprocess_account(account_id):
    # check account exists
    dash.models.Account.objects.get(pk=account_id)

    if not dash.models.AdGroup.objects.filter(campaign__account_id=account_id).exists():
        raise Exception("No ad groups exist for the selected account (pk={})".format(account_id))
