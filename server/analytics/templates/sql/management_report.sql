SELECT (CASE
            WHEN tags LIKE '%biz/agency%' THEN 'Agency'
            WHEN tags LIKE '%biz/CD%' THEN 'CD'
            WHEN tags LIKE '%biz/managed%' THEN 'Managed'
            WHEN tags LIKE '%biz/NES%' THEN 'NES'
            WHEN tags LIKE '%biz/OEN%' THEN 'OEN'
            WHEN tags LIKE '%biz/PaaS%' THEN 'PaaS'
            WHEN tags LIKE '%biz/internal%' THEN 'Internal'
            ELSE 'Untagged'
        END) AS customer_type,
       (CASE
            WHEN tags LIKE '%biz/big6%' THEN 'Big6'
            WHEN tags LIKE '%biz/indie%' THEN 'Indie'
            ELSE '-'
        END) AS client_size,
       (CASE
            WHEN tags LIKE '%biz/US%' THEN 'US'
            WHEN tags LIKE '%biz/intl%' THEN 'Intl'
            ELSE '-'
        END) AS region,
       sum(y_media) AS y_media,
       sum(y_fee) AS y_fee,
       sum(mtd_media) AS mtd_media,
       sum(mtd_fee) AS mtd_fee,
       (CASE
            WHEN date_trunc('month', CURRENT_DATE)::date = CURRENT_DATE::date THEN 0
            ELSE DATEDIFF (DAY, CURRENT_DATE, LAST_DAY(CURRENT_DATE))
        END) * sum(y_media) + sum(mtd_media) AS eof_media_projection1,
       (CASE
            WHEN date_trunc('month', CURRENT_DATE)::date = CURRENT_DATE::date THEN 0
            ELSE DATEDIFF (DAY, CURRENT_DATE, LAST_DAY(CURRENT_DATE))
        END) * sum(y_fee) + sum(mtd_fee) AS eof_fee_projection1,
       (CASE
            WHEN date_trunc('month', CURRENT_DATE)::date = CURRENT_DATE::date THEN 0
            ELSE DATEDIFF (DAY, CURRENT_DATE, LAST_DAY(CURRENT_DATE)) * sum(mtd_media) / DATEDIFF (DAY, date_trunc('month', CURRENT_DATE), CURRENT_DATE)
        END) + sum(mtd_media) AS eof_media_projection2,
       (CASE
            WHEN date_trunc('month', CURRENT_DATE)::date = CURRENT_DATE::date THEN 0
            ELSE DATEDIFF (DAY, CURRENT_DATE, LAST_DAY(CURRENT_DATE)) * sum(mtd_fee) / DATEDIFF (DAY, date_trunc('month', CURRENT_DATE), CURRENT_DATE)
        END) + sum(mtd_fee) AS eof_fee_projection2
FROM
  (SELECT y.agency_id,
          y.account_id,
          y.mtd_media,
          y.mtd_fee,
          y.y_media,
          y.y_fee,
          nvl(listagg(DISTINCT (CASE
                                    WHEN agency_id IS NULL THEN acct.name
                                    ELSE ayt.name
                                END), ' '),'') AS tags
   FROM
     (SELECT x.agency_id,
             x.account_id,
             sum(media + DATA) AS mtd_media,
             sum(fee) AS mtd_fee,
             sum(CASE
                     WHEN date = (CURRENT_DATE - interval '1 days')::date THEN media+DATA
                     ELSE 0
                 END) AS y_media,
             sum(CASE
                     WHEN date = (CURRENT_DATE - interval '1 days')::date THEN fee
                     ELSE 0
                 END) AS y_fee
      FROM
        (SELECT acc.agency_id AS agency_id,
                acc.id AS account_id,
                stats.date AS date,
                sum(stats.cost_nano::decimal)/1e9 AS media,
                sum(stats.data_cost_nano::decimal)/1e9 AS DATA,
                sum(stats.license_fee_nano::decimal)/1e9 AS fee
         FROM mv_account stats
         JOIN mv_rds_account acc ON acc.id = stats.account_id
         WHERE ((date_trunc('month', CURRENT_DATE)::date = CURRENT_DATE::date
                 AND stats.date >= date_trunc('month', CURRENT_DATE - interval '1 day')::date)
                OR (stats.date >= date_trunc('month', CURRENT_DATE)::date))
           AND stats.date < CURRENT_DATE::date
         GROUP BY 1,
                  2,
                  3) x
      GROUP BY 1,
               2) y
   LEFT JOIN
     (SELECT name,
             agency
      FROM mv_rds_agency_tag
      WHERE name LIKE 'biz/%'
      ORDER BY name) ayt ON ayt.agency = y.agency_id
   LEFT JOIN
     (SELECT name,
             account
      FROM mv_rds_account_tag
      WHERE name LIKE 'biz/%'
      ORDER BY name) acct ON acct.account = y.account_id
   GROUP BY 1,
            2,
            3,
            4,
            5,
            6) z
WHERE mtd_media > 0
  AND tags NOT LIKE '%biz/OEN%'
GROUP BY 1,
         2,
         3
ORDER BY 1,
         2,
         3
