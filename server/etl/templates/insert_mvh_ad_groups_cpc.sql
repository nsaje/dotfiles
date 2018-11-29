{% load backtosql_tags %}
INSERT INTO mvh_ad_groups_cpc (ad_group_id, cpc_micro)
VALUES {{ values }};
