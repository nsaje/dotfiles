CREATE TABLE IF NOT EXISTS MV_RDS_AGENCY (
  id                   integer PRIMARY KEY,
  name                 varchar(100),
  whitelabel           varchar(255),
  default_account_type varchar(100),
  sales_representative varchar(100) NULL,
  cs_representative    varchar(100) NULL,
  ob_representative    varchar(100) NULL
);


CREATE TABLE IF NOT EXISTS MV_RDS_SOURCE (
  id                           integer PRIMARY KEY,
  tracking_slug                varchar(50),
  bidder_slug                  varchar(50)  NULL,
  name                         varchar(127),
  maintenance                  boolean,
  deprecated                   boolean,
  released                     boolean,
  supports_retargeting         boolean,
  impression_trackers_count    SMALLINT,
  content_ad_submission_policy VARCHAR(50),
  content_ad_submission_type   varchar(50),
  source_type                  varchar(127) NULL
);

CREATE TABLE IF NOT EXISTS MV_RDS_ACCOUNT (
  id                           integer PRIMARY KEY,
  auto_archiving_enabled       boolean,
  currency                     varchar(30)  NULL,
  yahoo_account_id             integer      NULL,
  agency_id                    integer      NULL,
  account_sales_representative varchar(100) NULL,
  account_account_manager      varchar(100) NULL,
  account_cs_representative    varchar(100) NULL,
  account_ob_representative    varchar(100) NULL,
  archived                     BOOLEAN,
  account_type                 varchar(50),
  name                         varchar(127)
);

create TABLE IF NOT EXISTS MV_RDS_CAMPAIGN (
  id                       INTEGER PRIMARY KEY,
  name                     VARCHAR(127),
  type                     VARCHAR(100)  NULL,
  account_id               INTEGER,
  real_time_campaign_stop  BOOLEAN,
  campaign_manager         VARCHAR(100)  NULL,
  language                 varchar(50)   NULL,
  iab_category             VARCHAR(50),
  campaign_promotion_goal  VARCHAR(50),
  campaign_goal            VARCHAR(50),
  goal_quantity            VARCHAR(50),
  target_devices           JSON,
  target_placements        integer ARRAY NULL,
  target_os                JSON          NULL,
  target_region            JSON,
  exclusion_target_regions JSON,
  automatic_campaign_stop  BOOLEAN       NULL,
  landing_mode             BOOLEAN       NULL,
  autopilot                BOOLEAN,
  enable_ga_tracking       BOOLEAN,
  ga_tracking_type         INTEGER,
  enable_adobe_tracking    BOOLEAN,
  archived                 BOOLEAN
);

CREATE TABLE IF NOT EXISTS MV_RDS_CAMPAIGN_GOAL (
  id                         integer PRIMARY KEY,
  campaign_goal_type         VARCHAR(100),
  campaign_goal_primary      BOOLEAN,
  conversion_goal_id         INTEGER NULL,
  conversion_goal_pixel_slug INTEGER,
  impressions                INTEGER
);


CREATE TABLE IF NOT EXISTS MV_RDS_CONTENT_AD (
  id              integer PRIMARY KEY,
  ad_group_id     INTEGER,
  archived        BOOLEAN,
  amplify_review  BOOLEAN             NULL,
  label           VARCHAR(256),
  url             VARCHAR(2048),
  title           VARCHAR(256),
  display_url     VARCHAR(35),
  brand_name      VARCHAR(25),
  description     VARCHAR(150),
  call_to_action  VARCHAR(25),
  image_id        VARCHAR(256)        NULL,
  image_width     INTEGER             NULL,
  image_height    INTEGER             NULL,
  image_hash      VARCHAR(128)        NULL,
  crop_areas      VARCHAR(128)        NULL,
  image_crop      VARCHAR(25),
  state           INTEGER             NULL,
  tracker_urls    VARCHAR(2048) ARRAY NULL,
  additional_data JSON                NULL,
  video_asset_id  UUID                NULL,
  video_status    VARCHAR(100),
  video_name      VARCHAR(255),
  video_duration  INTEGER             NULL,
  video_formats   JSON                NULL,
  video_type      VARCHAR(30),
  video_vast_url  VARCHAR(2048)       NULL
);


CREATE TABLE IF NOT EXISTS MV_RDS_AD_GROUP (
  id                                      integer PRIMARY KEY,
  campaign_id                             INTEGER,
  amplify_review                          BOOLEAN           NULL,
  state                                   VARCHAR(20),
  cpc_cc                                  DECIMAL(10, 4)    NULL,
  local_cpc_cc                            DECIMAL(10, 4)    NULL,
  daily_budget_cc                         DECIMAL(10, 4)    NULL,
  target_devices                          JSON,
  target_placements                       VARCHAR(24) ARRAY NULL,
  target_os                               JSON              NULL,
  target_browsers                         JSON              NULL,
  exclusion_target_regions                JSON              NULL,
  retargeting_ad_groups                   JSON,
  exclusion_retargeting_ad_groups         JSON,
  bluekai_targeting                       JSON,
  interest_targeting                      JSON,
  exclusion_interest_targeting            JSON,
  audience_targeting                      JSON,
  exclusion_audience_targeting            JSON,
  archived                                BOOLEAN,
  brand_name                              VARCHAR(25),
  call_to_action                          VARCHAR(25),
  autopilot_state                         INTEGER           NULL,
  autopilot_daily_budget                  DECIMAL(10, 4)    NULL,
  local_autopilot_daily_budget            DECIMAL(10, 4)    NULL,
  landing_mode                            BOOLEAN           NULL,
  b1_sources_group_enabled                BOOLEAN,
  b1_sources_group_daily_budget           DECIMAL(10, 4)    NULL,
  local_b1_sources_group_daily_budget     DECIMAL(10, 4)    NULL,
  b1_sources_group_cpc_cc                 DECIMAL(10, 4),
  local_b1_sources_group_cpc_cc           DECIMAL(10, 4)    NULL,
  b1_sources_group_state                  VARCHAR(20),
  max_cpm                                 DECIMAL(10, 4)    NULL,
  local_max_cpm                           DECIMAL(10, 4)    NULL,
  delivery_type                           VARCHAR(20),
  click_capping_daily_ad_group_max_clicks INTEGER,
  click_capping_daily_click_budget        DECIMAL(10, 4)    NULL
);
