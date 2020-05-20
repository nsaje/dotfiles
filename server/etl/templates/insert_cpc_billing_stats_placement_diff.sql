{% load backtosql_tags %}

INSERT INTO stats_placement_diff (
    date, hour,
    agency_id, account_id, campaign_id, ad_group_id,
    media_source_type, media_source,
    publisher, placement_type, placement,
    spend, ssp_spend
)(
    SELECT
        stats_placement.date, stats_placement.hour,
        stats_placement.agency_id, stats_placement.account_id, stats_placement.campaign_id, stats_placement.ad_group_id,
        stats_placement.media_source_type, stats_placement.media_source,
        stats_placement.publisher, stats_placement.placement_type, stats_placement.placement,
        ((stats_placement.clicks * mvh_ad_groups_cpc.cpc_micro) - stats_placement.spend),
        ((stats_placement.clicks * mvh_ad_groups_cpc.cpc_micro) - stats_placement.spend)
    FROM stats_placement
    JOIN mvh_ad_groups_cpc ON mvh_ad_groups_cpc.ad_group_id=stats_placement.ad_group_id
    WHERE (stats_placement.date BETWEEN '{{ tzdate_from }}' AND '{{ tzdate_to }}')
        AND (
            (stats_placement.hour IS NULL AND stats_placement.date >= '{{ date_from }}' AND stats_placement.date <= '{{ date_to }}')
            OR (stats_placement.hour IS NOT NULL AND stats_placement.date > '{{ tzdate_from }}' AND stats_placement.date < '{{ tzdate_to }}')
            OR (
                stats_placement.hour IS NOT NULL AND (
                (stats_placement.date='{{ tzdate_from }}' AND stats_placement.hour >= '{{ tzhour_from }}')
                OR (stats_placement.date = '{{ tzdate_to }}' AND stats_placement.hour < '{{ tzhour_to }}')
                )
            )
        )
);
