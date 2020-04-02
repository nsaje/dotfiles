select {{breakdown}}, sum(impressions) as impressions, sum(clicks) as clicks, sum(spend) as spend
from (
  select convert_timezone('UTC', '{{timezone}}',
                          (date || ' ' || hour || ':00:00')::timestamp)::date as date,
         publisher,
         sum(impressions) as impressions,
         sum(clicks) as clicks,
         sum(spend::decimal)/1e6 as spend
  from stats
  where media_source = '{{bidder_slug}}'
        and outbrain_publisher_id IN {% autoescape off %}({{outbrain_publisher_ids}}){% endautoescape %}
        and date >= ('{{start_date}}'::date - interval '1 day')
        and date <= ('{{end_date}}'::date + interval '1 day')
  group by 1, 2
) stats
where date between '{{ start_date }}' and '{{ end_date }}'
group by {{breakdown}}
order by {{breakdown}}
