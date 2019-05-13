SUM(CASE WHEN {{ p }}slug='{{ slug }}' AND {{ p }}account_id={{ account_id }} AND {{ p }}conversion_window<={{ window }} AND {{ p }}type={{ type }} THEN conversion_count ELSE 0 END) {{ alias }}
