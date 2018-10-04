CREATE TEMP TABLE mvh_campaign_factors (
    date date not null encode delta,
    campaign_id integer not null encode lzo,

    pct_actual_spend decimal(22, 18) encode lzo,
    pct_license_fee decimal(22, 18) encode lzo,
    pct_margin decimal(22, 18) encode lzo
) sortkey(date, campaign_id)
