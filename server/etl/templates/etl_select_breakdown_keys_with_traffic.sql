SELECT
    date,
    source_id,
    content_ad_id
FROM
    mv_master
WHERE
    date BETWEEN %(date_from)s AND %(date_to)s
GROUP BY 1, 2, 3;