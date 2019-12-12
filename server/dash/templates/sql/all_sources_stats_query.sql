select to_char(date, 'YYYY-MM-DD') as date, source_id, sum(coalesce(impressions, 0)), sum(coalesce(cost_nano, 0))
from mv_account
where date between '{date_from}' and '{date_to}'
group by date, source_id
order by date