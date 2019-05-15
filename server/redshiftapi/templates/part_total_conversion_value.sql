SUM(CASE WHEN {{ p }}slug='{{ slug }}' AND {{ p }}account_id={{ account_id }} AND {{ p }}conversion_window<={{ window }} THEN conversion_value_nano ELSE 0 END)/1000000000.0 {{ alias }}
