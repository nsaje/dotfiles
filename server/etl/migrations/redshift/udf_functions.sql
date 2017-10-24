-- This file includes all UDF functions that need to be applied on Redshift cluster.

/*
Sums key values of jsons separated by a delimiter. Useful with LISTAGG aggregate function. LISTAGG is used
as a workaround until Redshift adds support for aggregate UDF functions.

IMPORTANT: Make sure you use the same delimiter as for LISTAGG.

Example:
SELECT
ad_group_id,
json_dict_sum(LISTAGG(conversions, '\n'), '\n')
FROM postclickstats
WHERE date='2016-05-23'
GROUP BY ad_group_id;
*/
CREATE OR REPLACE FUNCTION json_dict_sum (a varchar(max), delimiter varchar(2)) RETURNS varchar(max) IMMUTABLE as $$
      import json
      if not a:
          return ""

      d = {}
      for line in a.split(delimiter):
          line = line.strip()
          if not line:
              continue

          dicts = json.loads(line)
          for k, v in dicts.iteritems():
              if k not in d:
                  d[k] = 0
              d[k] += v

      return json.dumps(d)
$$ LANGUAGE plpythonu;
