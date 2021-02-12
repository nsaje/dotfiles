CREATE TEMP TABLE mvh_adgroup_structure (
    agency_id integer encode lzo,
    account_id integer encode lzo,
    campaign_id integer encode lzo,
    ad_group_id integer encode lzo
)
diststyle all
sortkey(ad_group_id, campaign_id, account_id, agency_id)
