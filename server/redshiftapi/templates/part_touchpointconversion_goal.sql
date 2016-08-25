SUM(CASE WHEN {{ p }}slug='{{ slug }}' AND {{ p }}account_id={{ account_id }} AND {{ p }}conversion_window<={{ window }} THEN conversion_count ELSE 0 END) {{ alias }}
