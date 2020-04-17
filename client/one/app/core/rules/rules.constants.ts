export enum RuleTargetType {
    Ad = 'AD',
    AdGroup = 'AD_GROUP',
    AdGroupPublisher = 'PUBLISHER',
    AdGroupCountry = 'COUNTRY',
    AdGroupRegion = 'REGION',
    AdGroupDma = 'DMA',
    AdGroupDevice = 'DEVICE',
    AdGroupOs = 'OS',
    AdGroupEnvironment = 'ENVIRONMENT',
    AdGroupSource = 'SOURCE',
}

export enum RuleActionType {
    IncreaseBid = 'INCREASE_BID',
    DecreaseBid = 'DECREASE_BID',
    IncreaseBidModifier = 'INCREASE_BID_MODIFIER',
    DecreaseBidModifier = 'DECREASE_BID_MODIFIER',
    IncreaseDailyBudget = 'INCREASE_BUDGET',
    DecreaseDailyBudget = 'DECREASE_BUDGET',
    TurnOff = 'TURN_OFF',
    Blacklist = 'BLACKLIST',
    SendEmail = 'SEND_EMAIL',
    AddToPublisherGroup = 'ADD_TO_PUBLISHER_GROUP',
}

export enum RuleActionFrequency {
    Day1 = '1_DAY',
    Days3 = '3_DAYS',
    Days7 = '7_DAYS',
}

export enum Macro {
    AgencyId = 'AGENCY_ID',
    AgencyName = 'AGENCY_NAME',
    AccountId = 'ACCOUNT_ID',
    AccountName = 'ACCOUNT_NAME',
    CampaignId = 'CAMPAIGN_ID',
    CampaignName = 'CAMPAIGN_NAME',
    AdGroupId = 'AD_GROUP_ID',
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupDailyCap = 'AD_GROUP_DAILY_CAP',
    CampaignBudget = 'CAMPAIGN_BUDGET',
    TotalSpendLastDay = 'TOTAL_SPEND_LAST_DAY',
    TotalSpendLastThreeDays = 'TOTAL_SPEND_LAST_3_DAYS',
    TotalSpendLastSevenDays = 'TOTAL_SPEND_LAST_7_DAYS',
    TotalSpendLastThirtyDays = 'TOTAL_SPEND_LAST_30_DAYS',
    TotalSpendLifetime = 'TOTAL_SPEND_LIFETIME',
    ClicksLastDay = 'CLICKS_LAST_DAY',
    ClicksLastThreeDays = 'CLICKS_LAST_3_DAYS',
    ClicksLastSevenDays = 'CLICKS_LAST_7_DAYS',
    ClicksLastThirtyDays = 'CLICKS_LAST_30_DAYS',
    ClicksLifetime = 'CLICKS_LIFETIME',
    ImpressionsLastDay = 'IMPRESSIONS_LAST_DAY',
    ImpressionsLastThreeDays = 'IMPRESSIONS_LAST_3_DAYS',
    ImpressionsLastSevenDays = 'IMPRESSIONS_LAST_7_DAYS',
    ImpressionsLastThirtyDays = 'IMPRESSIONS_LAST_30_DAYS',
    ImpressionsLifetime = 'IMPRESSIONS_LIFETIME',
    AvgCpcLastDay = 'AVG_CPC_LAST_DAY',
    AvgCpcLastThreeDays = 'AVG_CPC_LAST_3_DAYS',
    AvgCpcLastSevenDays = 'AVG_CPC_LAST_7_DAYS',
    AvgCpcLastThirtyDays = 'AVG_CPC_LAST_30_DAYS',
    AvgCpcLifetime = 'AVG_CPC_LIFETIME',
    AvgCpmLastDay = 'AVG_CPM_LAST_DAY',
    AvgCpmLastThreeDays = 'AVG_CPM_LAST_3_DAYS',
    AvgCpmLastSevenDays = 'AVG_CPM_LAST_7_DAYS',
    AvgCpmLastThirtyDays = 'AVG_CPM_LAST_30_DAYS',
    AvgCpmLifetime = 'AVG_CPM_LIFETIME',
    VisitsLastDay = 'VISITS_LAST_DAY',
    VisitsLastThreeDays = 'VISITS_LAST_3_DAYS',
    VisitsLastSevenDays = 'VISITS_LAST_7_DAYS',
    VisitsLastThirtyDays = 'VISITS_LAST_30_DAYS',
    VisitsLifetime = 'VISITS_LIFETIME',
    UniqueUsersLastDay = 'UNIQUE_USERS_LAST_DAY',
    UniqueUsersLastThreeDays = 'UNIQUE_USERS_LAST_3_DAYS',
    UniqueUsersLastSevenDays = 'UNIQUE_USERS_LAST_7_DAYS',
    UniqueUsersLastThirtyDays = 'UNIQUE_USERS_LAST_30_DAYS',
    UniqueUsersLifetime = 'UNIQUE_USERS_LIFETIME',
    NewUsersLastDay = 'NEW_USERS_LAST_DAY',
    NewUsersLastThreeDays = 'NEW_USERS_LAST_3_DAYS',
    NewUsersLastSevenDays = 'NEW_USERS_LAST_7_DAYS',
    NewUsersLastThirtyDays = 'NEW_USERS_LAST_30_DAYS',
    NewUsersLifetime = 'NEW_USERS_LIFETIME',
    ReturningUsersLastDay = 'RETURNING_USERS_LAST_DAY',
    ReturningUsersLastThreeDays = 'RETURNING_USERS_LAST_3_DAYS',
    ReturningUsersLastSevenDays = 'RETURNING_USERS_LAST_7_DAYS',
    ReturningUsersLastThirtyDays = 'RETURNING_USERS_LAST_30_DAYS',
    ReturningUsersLifetime = 'RETURNING_USERS_LIFETIME',
    PercentNewUsersLastDay = 'PERCENT_NEW_USERS_LAST_DAY',
    PercentNewUsersLastThreeDays = 'PERCENT_NEW_USERS_LAST_3_DAYS',
    PercentNewUsersLastSevenDays = 'PERCENT_NEW_USERS_LAST_7_DAYS',
    PercentNewUsersLastThirtyDays = 'PERCENT_NEW_USERS_LAST_30_DAYS',
    PercentNewUsersLifetime = 'PERCENT_NEW_USERS_LIFETIME',
    ClickDiscrepancyLastDay = 'CLICK_DISCREPANCY_LAST_DAY',
    ClickDiscrepancyLastThreeDays = 'CLICK_DISCREPANCY_LAST_3_DAYS',
    ClickDiscrepancyLastSevenDays = 'CLICK_DISCREPANCY_LAST_7_DAYS',
    ClickDiscrepancyLastThirtyDays = 'CLICK_DISCREPANCY_LAST_30_DAYS',
    ClickDiscrepancyLifetime = 'CLICK_DISCREPANCY_LIFETIME',
    PageviewsLastDay = 'PAGEVIEWS_LAST_DAY',
    PageviewsLastThreeDays = 'PAGEVIEWS_LAST_3_DAYS',
    PageviewsLastSevenDays = 'PAGEVIEWS_LAST_7_DAYS',
    PageviewsLastThirtyDays = 'PAGEVIEWS_LAST_30_DAYS',
    PageviewsLifetime = 'PAGEVIEWS_LIFETIME',
    PageviewsPerVisitLastDay = 'PAGEVIEWS_PER_VISIT_LAST_DAY',
    PageviewsPerVisitLastThreeDays = 'PAGEVIEWS_PER_VISIT_LAST_3_DAYS',
    PageviewsPerVisitLastSevenDays = 'PAGEVIEWS_PER_VISIT_LAST_7_DAYS',
    PageviewsPerVisitLastThirtyDays = 'PAGEVIEWS_PER_VISIT_LAST_30_DAYS',
    PageviewsPerVisitLifetime = 'PAGEVIEWS_PER_VISIT_LIFETIME',
    BouncedVisitsLastDay = 'BOUNCED_VISITS_LAST_DAY',
    BouncedVisitsLastThreeDays = 'BOUNCED_VISITS_LAST_3_DAYS',
    BouncedVisitsLastSevenDays = 'BOUNCED_VISITS_LAST_7_DAYS',
    BouncedVisitsLastThirtyDays = 'BOUNCED_VISITS_LAST_30_DAYS',
    BouncedVisitsLifetime = 'BOUNCED_VISITS_LIFETIME',
    NonBouncedVisitsLastDay = 'NON_BOUNCED_VISITS_LAST_DAY',
    NonBouncedVisitsLastThreeDays = 'NON_BOUNCED_VISITS_LAST_3_DAYS',
    NonBouncedVisitsLastSevenDays = 'NON_BOUNCED_VISITS_LAST_7_DAYS',
    NonBouncedVisitsLastThirtyDays = 'NON_BOUNCED_VISITS_LAST_30_DAYS',
    NonBouncedVisitsLifetime = 'NON_BOUNCED_VISITS_LIFETIME',
    BounceRateLastDay = 'BOUNCE_RATE_LAST_DAY',
    BounceRateLastThreeDays = 'BOUNCE_RATE_LAST_3_DAYS',
    BounceRateLastSevenDays = 'BOUNCE_RATE_LAST_7_DAYS',
    BounceRateLastThirtyDays = 'BOUNCE_RATE_LAST_30_DAYS',
    BounceRateLifetime = 'BOUNCE_RATE_LIFETIME',
    TotalSecondsLastDay = 'TOTAL_SECONDS_LAST_DAY',
    TotalSecondsLastThreeDays = 'TOTAL_SECONDS_LAST_3_DAYS',
    TotalSecondsLastSevenDays = 'TOTAL_SECONDS_LAST_7_DAYS',
    TotalSecondsLastThirtyDays = 'TOTAL_SECONDS_LAST_30_DAYS',
    TotalSecondsLifetime = 'TOTAL_SECONDS_LIFETIME',
    AvgTimeOnSiteLastDay = 'AVG_TIME_ON_SITE_LAST_DAY',
    AvgTimeOnSiteLastThreeDays = 'AVG_TIME_ON_SITE_LAST_3_DAYS',
    AvgTimeOnSiteLastSevenDays = 'AVG_TIME_ON_SITE_LAST_7_DAYS',
    AvgTimeOnSiteLastThirtyDays = 'AVG_TIME_ON_SITE_LAST_30_DAYS',
    AvgTimeOnSiteLifetime = 'AVG_TIME_ON_SITE_LIFETIME',
    AvgCostPerVisitLastDay = 'AVG_COST_PER_VISIT_LAST_DAY',
    AvgCostPerVisitLastThreeDays = 'AVG_COST_PER_VISIT_LAST_3_DAYS',
    AvgCostPerVisitLastSevenDays = 'AVG_COST_PER_VISIT_LAST_7_DAYS',
    AvgCostPerVisitLastThirtyDays = 'AVG_COST_PER_VISIT_LAST_30_DAYS',
    AvgCostPerVisitLifetime = 'AVG_COST_PER_VISIT_LIFETIME',
    AvgCostPerNewVisitorLastDay = 'AVG_COST_PER_NEW_VISITOR_LAST_DAY',
    AvgCostPerNewVisitorLastThreeDays = 'AVG_COST_PER_NEW_VISITOR_LAST_3_DAYS',
    AvgCostPerNewVisitorLastSevenDays = 'AVG_COST_PER_NEW_VISITOR_LAST_7_DAYS',
    AvgCostPerNewVisitorLastThirtyDays = 'AVG_COST_PER_NEW_VISITOR_LAST_30_DAYS',
    AvgCostPerNewVisitorLifetime = 'AVG_COST_PER_NEW_VISITOR_LIFETIME',
    AvgCostPerPageviewLastDay = 'AVG_COST_PER_PAGEVIEW_LAST_DAY',
    AvgCostPerPageviewLastThreeDays = 'AVG_COST_PER_PAGEVIEW_LAST_3_DAYS',
    AvgCostPerPageviewLastSevenDays = 'AVG_COST_PER_PAGEVIEW_LAST_7_DAYS',
    AvgCostPerPageviewLastThirtyDays = 'AVG_COST_PER_PAGEVIEW_LAST_30_DAYS',
    AvgCostPerPageviewLifetime = 'AVG_COST_PER_PAGEVIEW_LIFETIME',
    AvgCostPerNonBouncedVisitLastDay = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_DAY',
    AvgCostPerNonBouncedVisitLastThreeDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_3_DAYS',
    AvgCostPerNonBouncedVisitLastSevenDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_7_DAYS',
    AvgCostPerNonBouncedVisitLastThirtyDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_30_DAYS',
    AvgCostPerNonBouncedVisitLifetime = 'AVG_COST_PER_NON_BOUNCED_VISIT_LIFETIME',
    AvgCostPerMinuteLastDay = 'AVG_COST_PER_MINUTE_LAST_DAY',
    AvgCostPerMinuteLastThreeDays = 'AVG_COST_PER_MINUTE_LAST_3_DAYS',
    AvgCostPerMinuteLastSevenDays = 'AVG_COST_PER_MINUTE_LAST_7_DAYS',
    AvgCostPerMinuteLastThirtyDays = 'AVG_COST_PER_MINUTE_LAST_30_DAYS',
    AvgCostPerMinuteLifetime = 'AVG_COST_PER_MINUTE_LIFETIME',
    AvgCostPerConversionLastDay = 'AVG_COST_PER_CONVERSION_LAST_DAY',
    AvgCostPerConversionLastThreeDays = 'AVG_COST_PER_CONVERSION_LAST_3_DAYS',
    AvgCostPerConversionLastSevenDays = 'AVG_COST_PER_CONVERSION_LAST_7_DAYS',
    AvgCostPerConversionLastThirtyDays = 'AVG_COST_PER_CONVERSION_LAST_30_DAYS',
    AvgCostPerConversionLifetime = 'AVG_COST_PER_CONVERSION_LIFETIME',
    AvgCostPerConversionViewLastDay = 'AVG_COST_PER_CONVERSION_VIEW_LAST_DAY',
    AvgCostPerConversionViewLastThreeDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_3_DAYS',
    AvgCostPerConversionViewLastSevenDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_7_DAYS',
    AvgCostPerConversionViewLastThirtyDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_30_DAYS',
    AvgCostPerConversionViewLifetime = 'AVG_COST_PER_CONVERSION_VIEW_LIFETIME',
    AvgCostPerConversionTotalLastDay = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_DAY',
    AvgCostPerConversionTotalLastThreeDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_3_DAYS',
    AvgCostPerConversionTotalLastSevenDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_7_DAYS',
    AvgCostPerConversionTotalLastThirtyDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_30_DAYS',
    AvgCostPerConversionTotalLifetime = 'AVG_COST_PER_CONVERSION_TOTAL_LIFETIME',
}

export enum RuleConditionOperandType {
    AbsoluteValue = 'ABSOLUTE',
    CurrentDate = 'CURRENT_DATE',
    TotalSpend = 'TOTAL_SPEND',
    AverageDailyTotalSpend = 'AVERAGE_DAILY_TOTAL_SPEND',
    Impressions = 'IMPRESSIONS',
    Clicks = 'CLICKS',
    Ctr = 'CTR',
    Cpc = 'AVG_CPC',
    Cpm = 'AVG_CPM',
    Visits = 'VISITS',
    UniqueUsers = 'UNIQUE_USERS',
    NewUsers = 'NEW_USERS',
    ReturningUsers = 'RETURNING_USERS',
    PercentNewUsers = 'NEW_USERS_RATIO',
    ClickDiscrepancy = 'CLICK_DISCREPANCY',
    Pageviews = 'PAGEVIEWS',
    PageviewsPerVisit = 'PAGEVIEWS_PER_VISIT',
    BouncedVisits = 'BOUNCED_VISITS',
    NonBouncedVisits = 'NON_BOUNCED_VISITS',
    BounceRate = 'BOUNCE_RATE',
    TotalSeconds = 'TOTAL_SECONDS',
    TimeOnSite = 'AVG_TIME_ON_SITE',
    AvgCostPerConversion = 'AVG_COST_PER_CONVERSION',
    AvgCostPerConversionView = 'AVG_COST_PER_CONVERSION_VIEW',
    AvgCostPerConversionTotal = 'AVG_COST_PER_CONVERSION_TOTAL',
    CampaignBudget = 'CAMPAIGN_BUDGET',
    RemainingCampaignBudget = 'REMAINING_CAMPAIGN_BUDGET',
    CampaignBudgetMargin = 'CAMPAIGN_BUDGET_MARGIN',
    CampaignBudgetStartDate = 'CAMPAIGN_BUDGET_START_DATE',
    CampaignBudgetEndDate = 'CAMPAIGN_BUDGET_END_DATE',
    DaysSinceCampaignBudgetStart = 'DAYS_SINCE_CAMPAIGN_BUDGET_START',
    DaysUntilCampaignBudgetEnd = 'DAYS_UNTIL_CAMPAIGN_BUDGET_END',
    CtrCampaignGoal = 'CTR_CAMPAIGN_GOAL',
    CpcCampaignGoal = 'CPC_CAMPAIGN_GOAL',
    CpmCampaignGoal = 'CPM_CAMPAIGN_GOAL',
    PercentNewUsersCampaignGoal = 'PERCENT_NEW_USERS_CAMPAIGN_GOAL',
    PageviewsPerVisitCampaignGoal = 'PAGEVIEWS_PER_VISIT_CAMPAIGN_GOAL',
    BounceRateCampaignGoal = 'BOUNCE_RATE_CAMPAIGN_GOAL',
    TimeOnSiteCampaignGoal = 'TIME_ON_SITE_CAMPAIGN_GOAL',
    AccountName = 'ACCOUNT_NAME',
    AccountCreatedDate = 'ACCOUNT_CREATED_DATE',
    DaysSinceAccountCreated = 'DAYS_SINCE_ACCOUNT_CREATED',
    CampaignName = 'CAMPAIGN_NAME',
    CampaignCreatedDate = 'CAMPAIGN_CREATED_DATE',
    DaysSinceCampaignCreated = 'DAYS_SINCE_CAMPAIGN_CREATED',
    CampaignManager = 'CAMPAIGN_MANAGER',
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupCreatedDate = 'AD_GROUP_CREATED_DATE',
    DaysSinceAdGroupCreated = 'DAYS_SINCE_AD_GROUP_CREATED',
    AdGroupStartDate = 'AD_GROUP_START_DATE',
    AdGroupEndDate = 'AD_GROUP_END_DATE',
    AdGroupDailyCap = 'AD_GROUP_DAILY_CAP',
    AdTitle = 'AD_TITLE',
    AdLabel = 'AD_LABEL',
    AdCreatedDate = 'AD_CREATED_DATE',
    DaysSinceAdCreated = 'DAYS_SINCE_AD_CREATED',
}

export enum RuleConditionOperandGroup {
    TrafficAcquisition = 'Traffic acquisition',
    AudienceMetrics = 'Audience metrics',
    Conversions = 'Conversions & CPAs',
    Goals = 'Goals',
    Settings = 'Settings',
    Budget = 'Budget',
}

export enum RuleNotificationType {
    None = 'NONE',
    OnRuleRun = 'ON_RULE_RUN',
    OnRuleActionTriggered = 'ON_RULE_ACTION_TRIGGERED',
}

export enum RuleConditionOperator {
    LessThan = 'LESS_THAN',
    GreaterThan = 'GREATER_THAN',
    Contains = 'CONTAINS',
    NotContains = 'NOT_CONTAINS',
    Equals = 'EQUALS',
    NotEquals = 'NOT_EQUALS',
}

export enum TimeRange {
    LastDay = 'LAST_DAY',
    LastThreeDays = 'LAST_3_DAYS',
    LastSevenDays = 'LAST_7_DAYS',
    LastThirtyDays = 'LAST_30_DAYS',
    Lifetime = 'LIFETIME',
    NotApplicable = 'NOT_APPLICABLE',
}
