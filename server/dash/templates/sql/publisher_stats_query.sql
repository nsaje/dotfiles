select to_char(date, 'YYYY-MM-DD') as date, publisher, sum(coalesce(impressions, 0)), sum(coalesce(clicks, 0)), sum(coalesce(cost_nano, 0))
from mv_account_pubs
where source_id=%s and date=%s
group by date, publisher