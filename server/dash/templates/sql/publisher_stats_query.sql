select to_char(date, 'YYYY-MM-DD') as date,
       publisher,
       sum(coalesce(impressions, 0)),
       sum(coalesce(clicks, 0)),
       sum(coalesce(cost_nano::decimal, 0))/1e9
from mv_account_pubs
where source_id={{source_id}} and date='{{date}}'
group by date, publisher
