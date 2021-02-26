CREATE TEMP TABLE mvh_adgroup_structure (
    agency_id integer encode AZ64,
    account_id integer encode AZ64,
    campaign_id integer encode AZ64,
    ad_group_id integer encode AZ64,
    uses_source_groups boolean encode raw
)
diststyle all
sortkey(ad_group_id, campaign_id, account_id, agency_id)
