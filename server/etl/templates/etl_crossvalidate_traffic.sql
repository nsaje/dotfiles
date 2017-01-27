-- crossvalidate stats, new materialized views and old materialized views
-- derived views are crossvalidated in a separate job

WITH
    temp_stats AS (
        SELECT
            NVL(SUM(clicks), 0) AS clicks,
            NVL(SUM(impressions), 0) AS impressions,
            NVL(SUM(spend), 0) AS spend_micro,
            NVL(SUM(data_spend), 0) AS data_spend_micro
        FROM stats
        WHERE
            ((hour is null and date>=%(date_from)s AND date<=%(date_to)s)
            OR
            (hour is not null and date>%(tzdate_from)s AND date<%(tzdate_to)s)
            OR
            (hour IS NOT NULL AND (
                (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
                (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
            )))
    ),

    temp_contentadstats AS (
        SELECT
            NVL(SUM(clicks), 0) AS clicks,
            NVL(SUM(impressions), 0) AS impressions,
            NVL(SUM(cost_cc), 0) * 100.0 AS spend_micro,
            NVL(SUM(data_cost_cc), 0) * 100.0 AS data_spend_micro,
            NVL(SUM(effective_cost_nano), 0) AS effective_cost_nano,
            NVL(SUM(effective_data_cost_nano), 0) AS effective_data_cost_nano
        FROM contentadstats
        WHERE date>=%(date_from)s AND date<=%(date_to)s
    ),

    temp_master AS (
        SELECT
            NVL(SUM(clicks), 0) AS clicks,
            NVL(SUM(impressions), 0) AS impressions,
            NVL(SUM(cost_nano), 0) / 1000.0 AS spend_micro,
            NVL(SUM(data_cost_nano), 0) / 1000.0 AS data_spend_micro,
            NVL(SUM(effective_cost_nano), 0) AS effective_cost_nano,
            NVL(SUM(effective_data_cost_nano), 0) AS effective_data_cost_nano
        FROM mv_master
        WHERE date>=%(date_from)s AND date<=%(date_to)s
    )

SELECT
    -- these should match exactly, based on stats table
    a.clicks,
    a.clicks - b.clicks AS diff_s_ca_clicks,
    a.clicks - c.clicks AS diff_s_mv_clicks,
    a.impressions,
    a.impressions - b.impressions AS diff_s_ca_impressions,
    a.impressions - c.impressions AS diff_s_mv_impressions,
    a.spend_micro,
    a.spend_micro - b.spend_micro AS diff_s_ca_spend_micro,
    a.spend_micro - c.spend_micro AS diff_s_mv_spend_micro,
    a.data_spend_micro,
    a.data_spend_micro - b.data_spend_micro AS diff_s_ca_data_spend_micro,
    a.data_spend_micro - c.data_spend_micro AS diff_s_mv_data_spend_micro,

    -- match exactly, mv_master vs contentadstats
    b.effective_cost_nano - c.effective_cost_nano AS diff_ca_mv_effective_cost_nano,

    -- how much overspend
    a.spend_micro * 1000 AS spend_nano,
    c.effective_cost_nano AS effective_cost_nano,
    a.spend_micro * 1000 - c.effective_cost_nano AS overspend_nano
FROM temp_stats a, temp_contentadstats b, temp_master c;