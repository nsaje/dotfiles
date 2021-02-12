CREATE TEMP TABLE mvh_currency_exchange_rates (
    date date not null encode AZ64,
    account_id integer not null encode AZ64,
    exchange_rate decimal(10, 4) encode AZ64
)
diststyle all
sortkey(date, account_id)
