DELETE FROM partnerstats WHERE utc_date >= (current_date - interval '2 day');
