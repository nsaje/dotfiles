import dash.models
from dash import stats_helper
from collections import defaultdict


def fetch_ad_group_content_ad_metrics(user, ad_group, start_date, end_date, limit=10):
    stats = stats_helper.get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=['content_ad'],
        ignore_diff_rows=True,
        constraints={'ad_group': ad_group.id}
    )
    dd_ads = _deduplicate_content_ad_titles(ad_group=ad_group)
    return _extract_ends(dd_ads, stats)


def fetch_campaign_content_ad_metrics(user, campaign, start_date, end_date, limit=10):
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


def _extract_ends(deduplicated_ads, stats, limit=10):
    mapped_stats = {stat['content_ad']: stat for stat in stats}
    dd_cad_metric = []
    for title, caids in deduplicated_ads.iteritems():
        clicks = sum(map(lambda caid: mapped_stats.get(caid, {}).get('clicks', 0) or 0, caids))
        impressions = sum(map(lambda caid: mapped_stats.get(caid, {}).get('impressions', 0) or 0, caids))
        metric = float(clicks) / impressions if impressions > 0 else None
        dd_cad_metric.append({
            'summary': title,
            'metric': '{:.2f}%'.format(metric*100) if metric else None,
            'value': metric or 0,
            'clicks': clicks or 0,
        })

    top_cads = sorted(dd_cad_metric, key=lambda dd_cad: dd_cad['value'], reverse=True)[:limit]

    active_dd_cad_metric = [cad_metric for cad_metric in dd_cad_metric if cad_metric['clicks'] >= 10]
    bott_cads = sorted(active_dd_cad_metric, key=lambda dd_cad: dd_cad['value'])[:limit]
    return [{'summary': cad['summary'], 'metric': cad['metric']} for cad in top_cads],\
        [{'summary': cad['summary'], 'metric': cad['metric']} for cad in bott_cads]


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
