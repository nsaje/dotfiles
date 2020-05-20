DELETE FROM partnerstats WHERE utc_date >= (current_date - interval '1 day');
