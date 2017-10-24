-- Do the same thing for mv_master_diff, mv_pubs_master
-- reverse mapping to original values

INSERT INTO mv_master_new (
SELECT
    date,
    source_id,

    account_id,
    campaign_id,
    ad_group_id,
    content_ad_id,

    CASE WHEN publisher ILIKE 'unknown' THEN NULL
         ELSE publisher
    END AS publisher,
    CASE WHEN publisher ILIKE 'unknown' THEN '__' || source_id
         ELSE publisher || '__' || source_id
    END AS publisher_source_id,

    CASE
        WHEN device_type = 3 THEN 4 -- mobile
        WHEN device_type = 1 THEN 2 -- desktop
        WHEN device_type = 2 THEN 5 -- tablet
        ELSE NULL                   -- undefined
    END AS device_type,
    NULL AS device_os,
    NULL AS device_os_version,
    NULL AS placement_medium,

    NULLIF(placement_type, 0) AS placement_type,
    NULLIF(video_playback_method, 0) AS video_playback_method,

    NULLIF(TRIM(UPPER(country)), '') AS country,
    CASE WHEN state ILIKE '%-%' THEN NULLIF(TRIM(UPPER(state)), '')
         ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
    END AS state,
    CASE WHEN country ILIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
         ELSE NULL
    END AS dma,
    NULLIF(city_id, 0) AS city_id,

    CASE WHEN age=1 THEN '18-20'
         WHEN age=2 THEN '21-29'
         WHEN age=3 THEN '30-39'
         WHEN age=4 THEN '40-49'
         WHEN age=5 THEN '50-64'
         WHEN age=6 THEN '65+'
         ELSE NULL
    END AS age,
    CASE WHEN gender=1 THEN 'male'
         WHEN gender=2 THEN 'female'
         ELSE NULL
    END AS gender,
    CASE
        WHEN gender=1             AND age=1 THEN '18-20 male'
        WHEN gender=2             AND age=1 THEN '18-20 female'
        WHEN gender NOT IN (1, 2) AND age=1 THEN '18-20 '
        WHEN gender=1             AND age=2 THEN '21-29 male'
        WHEN gender=2             AND age=2 THEN '21-29 female'
        WHEN gender NOT IN (1, 2) AND age=2 THEN '21-29 '
        WHEN gender=1             AND age=3 THEN '30-39 male'
        WHEN gender=2             AND age=3 THEN '30-39 female'
        WHEN gender NOT IN (1, 2) AND age=3 THEN '30-39 '
        WHEN gender=1             AND age=4 THEN '40-49 male'
        WHEN gender=2             AND age=4 THEN '40-49 female'
        WHEN gender NOT IN (1, 2) AND age=4 THEN '40-49 '
        WHEN gender=1             AND age=5 THEN '50-64 male'
        WHEN gender=2             AND age=5 THEN '50-64 female'
        WHEN gender NOT IN (1, 2) AND age=5 THEN '50-64 '
        WHEN gender=1             AND age=6 THEN '65+ male'
        WHEN gender=2             AND age=6 THEN '65+ female'
        WHEN gender NOT IN (1, 2) AND age=6 THEN '65+ '
        ELSE NULL
    END AS age_gender,

    impressions,
    clicks,
    cost_nano,
    data_cost_nano,

    visits,
    new_visits,
    bounced_visits,
    pageviews,
    total_time_on_site,

    effective_cost_nano,
    effective_data_cost_nano,
    license_fee_nano,
    margin_nano,

    users,
    returning_users,

    video_start,
    video_first_quartile,
    video_midpoint,
    video_third_quartile,
    video_complete,
    video_progress_3s
FROM mv_master
);

-----



INSERT INTO mv_master_pubs (
SELECT
    date,
    source_id,

    account_id,
    campaign_id,
    ad_group_id,

    CASE WHEN publisher ILIKE 'unknown' THEN NULL
         ELSE publisher
    END AS publisher,
    CASE WHEN publisher ILIKE 'unknown' THEN '__' || source_id
         ELSE publisher || '__' || source_id
    END AS publisher_source_id,
    external_id,

    CASE
        WHEN device_type = 3 THEN 4 -- mobile
        WHEN device_type = 1 THEN 2 -- desktop
        WHEN device_type = 2 THEN 5 -- tablet
        ELSE NULL                   -- undefined
    END AS device_type,
    NULL AS device_os,
    NULL AS device_os_version,
    NULL AS placement_medium,

    NULLIF(placement_type, 0) AS placement_type,
    NULLIF(video_playback_method, 0) AS video_playback_method,

    NULLIF(TRIM(UPPER(country)), '') AS country,
    CASE WHEN state ILIKE '%-%' THEN NULLIF(TRIM(UPPER(state)), '')
         ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
    END AS state,
    CASE WHEN country ILIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
         ELSE NULL
    END AS dma,
    NULLIF(city_id, 0) AS city_id,

    CASE WHEN age=1 THEN '18-20'
         WHEN age=2 THEN '21-29'
         WHEN age=3 THEN '30-39'
         WHEN age=4 THEN '40-49'
         WHEN age=5 THEN '50-64'
         WHEN age=6 THEN '65+'
         ELSE NULL
    END AS age,
    CASE WHEN gender=1 THEN 'male'
         WHEN gender=2 THEN 'female'
         ELSE NULL
    END AS gender,
    CASE
        WHEN gender=1             AND age=1 THEN '18-20 male'
        WHEN gender=2             AND age=1 THEN '18-20 female'
        WHEN gender NOT IN (1, 2) AND age=1 THEN '18-20 '
        WHEN gender=1             AND age=2 THEN '21-29 male'
        WHEN gender=2             AND age=2 THEN '21-29 female'
        WHEN gender NOT IN (1, 2) AND age=2 THEN '21-29 '
        WHEN gender=1             AND age=3 THEN '30-39 male'
        WHEN gender=2             AND age=3 THEN '30-39 female'
        WHEN gender NOT IN (1, 2) AND age=3 THEN '30-39 '
        WHEN gender=1             AND age=4 THEN '40-49 male'
        WHEN gender=2             AND age=4 THEN '40-49 female'
        WHEN gender NOT IN (1, 2) AND age=4 THEN '40-49 '
        WHEN gender=1             AND age=5 THEN '50-64 male'
        WHEN gender=2             AND age=5 THEN '50-64 female'
        WHEN gender NOT IN (1, 2) AND age=5 THEN '50-64 '
        WHEN gender=1             AND age=6 THEN '65+ male'
        WHEN gender=2             AND age=6 THEN '65+ female'
        WHEN gender NOT IN (1, 2) AND age=6 THEN '65+ '
        ELSE NULL
    END AS age_gender,

    impressions,
    clicks,
    cost_nano,
    data_cost_nano,

    visits,
    new_visits,
    bounced_visits,
    pageviews,
    total_time_on_site,

    effective_cost_nano,
    effective_data_cost_nano,
    license_fee_nano,
    margin_nano,

    users,
    returning_users,

    video_start,
    video_first_quartile,
    video_midpoint,
    video_third_quartile,
    video_complete,
    video_progress_3s
FROM mv_pubs_master
);

------


INSERT INTO mv_conversions_new (
SELECT
    date,
    source_id,

    account_id,
    campaign_id,
    ad_group_id,
    content_ad_id,

    CASE WHEN publisher ILIKE 'unknown' THEN NULL
         ELSE publisher
    END AS publisher,
    CASE WHEN publisher ILIKE 'unknown' THEN '__' || source_id
         ELSE publisher || '__' || source_id
    END AS publisher_source_id,

    slug,

    conversion_count

FROM mv_conversions
);


-----

INSERT INTO mv_touchpointconversions_new (
SELECT
      date,
      source_id,

      account_id,
      campaign_id,
      ad_group_id,
      content_ad_id,

      CASE WHEN publisher ILIKE 'unknown' THEN NULL
      ELSE publisher
      END AS publisher,
      CASE WHEN publisher ILIKE 'unknown' THEN '__' || source_id
      ELSE publisher || '__' || source_id
      END AS publisher_source_id,

      slug,
      conversion_window,
      conversion_label,

      touchpoint_count,
      conversion_count,
      conversion_value_nano

FROM mv_touchpointconversions
);


---  DEPLOY STEP ----

begin;
ALTER TABLE mv_master RENAME TO mv_master_old;
ALTER TABLE mv_master_new RENAME TO mv_master;

ALTER TABLE mv_master_diff RENAME TO mv_master_diff_old;
ALTER TABLE mv_master_diff_new RENAME TO mv_master_diff;

ALTER TABLE mv_pubs_master RENAME TO mv_pubs_master_old;
ALTER TABLE mv_pubs_master_new RENAME TO mv_pubs_master;

ALTER TABLE mv_conversions RENAME TO mv_conversions_old;
ALTER TABLE mv_conversions_new RENAME TO mv_conversions;

ALTER TABLE mv_touchpointconversions RENAME TO mv_touchpointconversions_old;
ALTER TABLE mv_touchpointconversions_new RENAME TO mv_touchpointconversions;
commit;
