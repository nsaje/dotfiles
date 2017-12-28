import dash.models
from collections import defaultdict

import redshiftapi.api_breakdowns
import stats.api_breakdowns

CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10
MIN_WORST_PERFORMER_CLICKS = 20
MIN_BEST_PERFORMER_CLICKS = 20


def fetch_campaign_content_ad_metrics(user, campaign, start_date, end_date):
    goals = stats.api_breakdowns.get_goals({'campaign': campaign}, ['content_ad_id'])
    query_results = redshiftapi.api_breakdowns.query_all(
        breakdown=['content_ad_id'],
        constraints={
            'date__gte': start_date,
            'date__lte': end_date,
            'campaign_id': campaign.id,
        },
        parents=None,
        goals=goals,
        use_publishers_view=False,
    )
    dd_ads = _deduplicate_content_ad_titles(campaign=campaign)
    return _extract_ends(dd_ads, query_results)


def _extract_ends(deduplicated_ads, stats):
    mapped_stats = {stat['content_ad_id']: stat for stat in stats}
    dd_cad_metric = []
    for title, caids in deduplicated_ads.iteritems():
        dd_cad_metric.append(_extract_ctr_metric(title, caids, mapped_stats))

    active_metrics = [cad_metric for cad_metric in dd_cad_metric if
                      cad_metric['clicks'] >= MIN_BEST_PERFORMER_CLICKS]

    top_cads = sorted(
        active_metrics,
        key=lambda dd_cad: dd_cad['value'],
        reverse=True)[:CONTENT_INSIGHTS_TABLE_ROW_COUNT]

    active_metrics = [cad_metric for cad_metric in dd_cad_metric if
                      cad_metric['clicks'] >= MIN_WORST_PERFORMER_CLICKS]

    bott_cads = sorted(
        active_metrics,
        key=lambda dd_cad: dd_cad['value'])[:CONTENT_INSIGHTS_TABLE_ROW_COUNT]
    return [{'summary': cad['summary'], 'metric': cad['metric']} for cad in top_cads],\
        [{'summary': cad['summary'], 'metric': cad['metric']} for cad in bott_cads]


def _extract_ctr_metric(title, caids, mapped_stats):
    clicks = sum(map(lambda caid: mapped_stats.get(caid, {}).get('clicks', 0) or 0, caids))
    impressions = sum(map(lambda caid: mapped_stats.get(caid, {}).get('impressions', 0) or 0, caids))
    metric = float(clicks) / impressions if impressions > 0 else None
    return {
        'summary': title,
        'metric': '{:.2f}%'.format(metric * 100) if metric else None,
        'value': metric or 0,
        'clicks': clicks or 0,
    }


def _deduplicate_content_ad_titles(campaign=None, ad_group=None):
    ads = dash.models.ContentAd.objects.all()

    if campaign is not None:
        ads = ads.filter(ad_group__campaign=campaign)
    if ad_group is not None:
        ads = ads.filter(ad_group=ad_group)

    ads = ads.exclude_archived().values_list('id', 'title')
    ret = defaultdict(list)
    for caid, title in ads:
        ret[title].append(caid)
    return ret
