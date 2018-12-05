SELECT *
FROM (SELECT u.ad_group_id, (sum(u.spend) / sum(nullif(u.clicks, 0))) as ecpc, mvh_ad_groups_cpc.cpc_micro as cpc
      FROM (select * from stats_diff
            union all
            select * from stats) u
             JOIN mvh_ad_groups_cpc on mvh_ad_groups_cpc.ad_group_id = u.ad_group_id
      WHERE (u.date BETWEEN '{{ tzdate_from }}' AND '{{ tzdate_to }}')
        AND (
                (u.hour IS NULL AND u.date >= '{{ date_from }}' AND u.date <= '{{ date_to }}')
                  OR (u.hour IS NOT NULL AND u.date > '{{ tzdate_from }}' AND u.date < '{{ tzdate_to }}')
                  OR (
                    u.hour IS NOT NULL AND (
                        (u.date = '{{ tzdate_from }}' AND u.hour >= '{{ tzhour_from }}')
                          OR (u.date = '{{ tzdate_to }}' AND u.hour < '{{ tzhour_to }}')
                        )
                    )
                )
      GROUP BY u.ad_group_id, cpc) cpc_query
WHERE ecpc != cpc