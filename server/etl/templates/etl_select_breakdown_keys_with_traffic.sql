SELECT
    date,
    source_id,
    content_ad_id
FROM
    mv_master
WHERE
    date=%(date)s
GROUP BY 1, 2, 3;