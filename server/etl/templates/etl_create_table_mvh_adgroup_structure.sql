CREATE TABLE mvh_adgroup_structure (
      agency_id int2 encode lzo,
      account_id int2 encode lzo,
      campaign_id int2 encode lzo,
      ad_group_id int2 encode lzo
) sortkey(ad_group_id, campaign_id, account_id, agency_id)