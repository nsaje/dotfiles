{% load backtosql_tags %}

INSERT INTO stats_diff
(date, hour, media_source_type, media_source, content_ad_id, ad_group_id, device_type, device_os,device_os_version,
 country, state, dma, city_id, zem_placement_type, publisher, spend, ssp_spend, campaign_id, account_id, agency_id)

(SELECT stats.date, stats.hour, stats.media_source_type, stats.media_source, stats.content_ad_id,
    stats.ad_group_id, stats.device_type, stats.device_os, stats.device_os_version, stats.country, stats.state,
    stats.dma, stats.city_id, stats.zem_placement_type, stats.publisher, ((stats.clicks * mvh_ad.cpc_micro) - stats.spend), ((stats.clicks * mvh_ad.cpc_micro) - stats.spend),
    stats.campaign_id, stats.account_id, stats.agency_id
    FROM stats
    JOIN mvh_ad_groups_cpc AS mvh_ad ON mvh_ad.ad_group_id=stats.ad_group_id
    WHERE (stats.date BETWEEN '{{ tzdate_from }}' AND '{{ tzdate_to }}')
    AND (
          (stats.hour IS NULL AND stats.date >= '{{ date_from }}' AND stats.date <= '{{ date_to }}')
          OR (stats.hour IS NOT NULL AND stats.date > '{{ tzdate_from }}' AND stats.date < '{{ tzdate_to }}')
          OR (
                stats.hour IS NOT NULL AND (
                  (stats.date='{{ tzdate_from }}' AND stats.hour >= '{{ tzhour_from }}')
                  OR (stats.date = '{{ tzdate_to }}' AND stats.hour < '{{ tzhour_to }}')
                )
            )
    )
);
