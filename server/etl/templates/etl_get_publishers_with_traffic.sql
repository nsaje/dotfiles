SELECT
    ad_group_id,
    publisher,
    source_id,
    MAX(publisher || '__' || source_id) publisher_id,
    SUM(clicks) AS clicks,
    SUM(impressions) AS impressions
FROM
    mv_adgroup_pubs
WHERE
    ad_group_id=ANY(%(ad_group_id)s) AND
    date BETWEEN %(date_from)s AND %(date_to)s
GROUP BY ad_group_id, publisher, source_id
HAVING SUM(clicks) > 0 OR SUM(impressions) > 0
ORDER BY ad_group_id;
