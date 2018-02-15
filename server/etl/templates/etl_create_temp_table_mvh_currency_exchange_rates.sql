CREATE TEMP TABLE mvh_currency_exchange_rates (
    date date not null encode delta,
    account_id integer not null encode lzo,
    exchange_rate decimal(10, 4) encode lzo
) sortkey(date, account_id);
