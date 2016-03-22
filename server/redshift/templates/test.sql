SELECT {{ breakdown }}, {{ aggreates }}
FROM contentadstats
WHERE date BETWEEN {{ date_from }} AND {{ date_to }} AND account_id IN ({{ account_ids|join:',' }})
ORDER BY {{ order }}
OFFSET {{ offset }}
LIMIT {{ limit }};



SELECT {{ breakdown.prefixed('t') }}, {{ aggregates.prefixed('t') }}
FROM (
     SELECT
          {{ breakdown.prefixed('tt') }},
          {{ aggregates.prefixed('tt') }},
          ROW_NUMBER() OVER (PARTITION BY breakdown[:-1].prefixed('tt') ORDER BY {{ order }})
     FROM
        {{ view }} tt
     WHERE
        dt BETWEEN ? AND ?
        AND {{ constraints }}
     GROUP BY {{ breakdown.ordinal() }}
     ORDER BY {{ order }}
     ) t
WHERE {{ page.lvl_4.start }}
ORDER BY {{ order.ordinal() }}
OFFSET {{ page.start }}
LIMIT {{ page.start + page.size }}


-- Aggregates
-- Name: SUM
SUM({{ prefix }}{{ db_column }}) {{ unique_name }}
