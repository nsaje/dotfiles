CREATE TEMP TABLE mvh_campaign_factors (
    date date not null encode AZ64,
    campaign_id integer not null encode AZ64,

    pct_actual_spend decimal(22, 18) encode AZ64,
    pct_service_fee decimal(22, 18) encode AZ64,
    pct_license_fee decimal(22, 18) encode AZ64,
    pct_margin decimal(22, 18) encode AZ64
)
diststyle all
sortkey(date, campaign_id)
