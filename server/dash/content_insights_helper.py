import dash.models
from dash import stats_helper
from collections import defaultdict

CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10
MIN_WORST_PERFORMER_CLICKS = 10


def fetch_campaign_content_ad_metrics(user, campaign, start_date, end_date):
    stats = stats_helper.get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=['content_ad'],
        ignore_diff_rows=True,
        constraints={'campaign': campaign.id}
    )
    dd_ads = _deduplicate_content_ad_titles(campaign=campaign)
    return _extract_ends(dd_ads, stats)


def _extract_ends(deduplicated_ads, stats):
    mapped_stats = {stat['content_ad']: stat for stat in stats}
    dd_cad_metric = []
    for title, caids in deduplicated_ads.iteritems():
        dd_cad_metric.append(_extract_metric(title, caids, mapped_stats))

    top_cads = sorted(
        dd_cad_metric,
        key=lambda dd_cad: dd_cad['value'],
        reverse=True)[:CONTENT_INSIGHTS_TABLE_ROW_COUNT]

    active_metrics = [cad_metric for cad_metric in dd_cad_metric if
                      cad_metric['clicks'] >= MIN_WORST_PERFORMER_CLICKS]

    bott_cads = sorted(
        active_metrics,
        key=lambda dd_cad: dd_cad['value'])[:CONTENT_INSIGHTS_TABLE_ROW_COUNT]
    return [{'summary': cad['summary'], 'metric': cad['metric']} for cad in top_cads],\
        [{'summary': cad['summary'], 'metric': cad['metric']} for cad in bott_cads]


def _extract_metric(title, caids, mapped_stats):
    clicks = sum(map(lambda caid: mapped_stats.get(caid, {}).get('clicks', 0) or 0, caids))
    impressions = sum(map(lambda caid: mapped_stats.get(caid, {}).get('impressions', 0) or 0, caids))
    metric = float(clicks) / impressions if impressions > 0 else None
    return {
        'summary': title,
        'metric': '{:.2f}%'.format(metric*100) if metric else None,
        'value': metric or 0,
        'clicks': clicks or 0,
    }


def _deduplicate_content_ad_titles(campaign=None, ad_group=None):
    ads = dash.models.ContentAd.objects.all()

    if campaign is not None:
        ads = ads.filter(
           ad_group__campaign=campaign
        )
    if ad_group is not None:
        ads = ads.filter(
           ad_group=ad_group
        )

    ads = ads.exclude_archived().values_list('id', 'title')
    ret = defaultdict(list)
    for caid, title in ads:
        ret[title].append(caid)
    return ret
