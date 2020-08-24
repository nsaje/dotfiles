export enum RuleTargetType {
    Ad = 'AD',
    AdGroup = 'AD_GROUP',
    AdGroupPublisher = 'PUBLISHER',
    AdGroupCountry = 'COUNTRY',
    AdGroupRegion = 'STATE',
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
    Day1 = 24,
    Days3 = 72,
    Days7 = 168,
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
    TotalSpendLastSixtyDays = 'TOTAL_SPEND_LAST_60_DAYS',
    ClicksLastDay = 'CLICKS_LAST_DAY',
    ClicksLastThreeDays = 'CLICKS_LAST_3_DAYS',
    ClicksLastSevenDays = 'CLICKS_LAST_7_DAYS',
    ClicksLastThirtyDays = 'CLICKS_LAST_30_DAYS',
    ClicksLastSixtyDays = 'CLICKS_LAST_60_DAYS',
    ImpressionsLastDay = 'IMPRESSIONS_LAST_DAY',
    ImpressionsLastThreeDays = 'IMPRESSIONS_LAST_3_DAYS',
    ImpressionsLastSevenDays = 'IMPRESSIONS_LAST_7_DAYS',
    ImpressionsLastThirtyDays = 'IMPRESSIONS_LAST_30_DAYS',
    ImpressionsLastSixtyDays = 'IMPRESSIONS_LAST_60_DAYS',
    AvgCpcLastDay = 'AVG_CPC_LAST_DAY',
    AvgCpcLastThreeDays = 'AVG_CPC_LAST_3_DAYS',
    AvgCpcLastSevenDays = 'AVG_CPC_LAST_7_DAYS',
    AvgCpcLastThirtyDays = 'AVG_CPC_LAST_30_DAYS',
    AvgCpcLastSixtyDays = 'AVG_CPC_LAST_60_DAYS',
    AvgCpmLastDay = 'AVG_CPM_LAST_DAY',
    AvgCpmLastThreeDays = 'AVG_CPM_LAST_3_DAYS',
    AvgCpmLastSevenDays = 'AVG_CPM_LAST_7_DAYS',
    AvgCpmLastThirtyDays = 'AVG_CPM_LAST_30_DAYS',
    AvgCpmLastSixtyDays = 'AVG_CPM_LAST_60_DAYS',
    VisitsLastDay = 'VISITS_LAST_DAY',
    VisitsLastThreeDays = 'VISITS_LAST_3_DAYS',
    VisitsLastSevenDays = 'VISITS_LAST_7_DAYS',
    VisitsLastThirtyDays = 'VISITS_LAST_30_DAYS',
    VisitsLastSixtyDays = 'VISITS_LAST_60_DAYS',
    UniqueUsersLastDay = 'UNIQUE_USERS_LAST_DAY',
    UniqueUsersLastThreeDays = 'UNIQUE_USERS_LAST_3_DAYS',
    UniqueUsersLastSevenDays = 'UNIQUE_USERS_LAST_7_DAYS',
    UniqueUsersLastThirtyDays = 'UNIQUE_USERS_LAST_30_DAYS',
    UniqueUsersLastSixtyDays = 'UNIQUE_USERS_LAST_60_DAYS',
    NewUsersLastDay = 'NEW_USERS_LAST_DAY',
    NewUsersLastThreeDays = 'NEW_USERS_LAST_3_DAYS',
    NewUsersLastSevenDays = 'NEW_USERS_LAST_7_DAYS',
    NewUsersLastThirtyDays = 'NEW_USERS_LAST_30_DAYS',
    NewUsersLastSixtyDays = 'NEW_USERS_LAST_60_DAYS',
    ReturningUsersLastDay = 'RETURNING_USERS_LAST_DAY',
    ReturningUsersLastThreeDays = 'RETURNING_USERS_LAST_3_DAYS',
    ReturningUsersLastSevenDays = 'RETURNING_USERS_LAST_7_DAYS',
    ReturningUsersLastThirtyDays = 'RETURNING_USERS_LAST_30_DAYS',
    ReturningUsersLastSixtyDays = 'RETURNING_USERS_LAST_60_DAYS',
    PercentNewUsersLastDay = 'PERCENT_NEW_USERS_LAST_DAY',
    PercentNewUsersLastThreeDays = 'PERCENT_NEW_USERS_LAST_3_DAYS',
    PercentNewUsersLastSevenDays = 'PERCENT_NEW_USERS_LAST_7_DAYS',
    PercentNewUsersLastThirtyDays = 'PERCENT_NEW_USERS_LAST_30_DAYS',
    PercentNewUsersLastSixtyDays = 'PERCENT_NEW_USERS_LAST_60_DAYS',
    ClickDiscrepancyLastDay = 'CLICK_DISCREPANCY_LAST_DAY',
    ClickDiscrepancyLastThreeDays = 'CLICK_DISCREPANCY_LAST_3_DAYS',
    ClickDiscrepancyLastSevenDays = 'CLICK_DISCREPANCY_LAST_7_DAYS',
    ClickDiscrepancyLastThirtyDays = 'CLICK_DISCREPANCY_LAST_30_DAYS',
    ClickDiscrepancyLastSixtyDays = 'CLICK_DISCREPANCY_LAST_60_DAYS',
    PageviewsLastDay = 'PAGEVIEWS_LAST_DAY',
    PageviewsLastThreeDays = 'PAGEVIEWS_LAST_3_DAYS',
    PageviewsLastSevenDays = 'PAGEVIEWS_LAST_7_DAYS',
    PageviewsLastThirtyDays = 'PAGEVIEWS_LAST_30_DAYS',
    PageviewsLastSixtyDays = 'PAGEVIEWS_LAST_60_DAYS',
    PageviewsPerVisitLastDay = 'PAGEVIEWS_PER_VISIT_LAST_DAY',
    PageviewsPerVisitLastThreeDays = 'PAGEVIEWS_PER_VISIT_LAST_3_DAYS',
    PageviewsPerVisitLastSevenDays = 'PAGEVIEWS_PER_VISIT_LAST_7_DAYS',
    PageviewsPerVisitLastThirtyDays = 'PAGEVIEWS_PER_VISIT_LAST_30_DAYS',
    PageviewsPerVisitLastSixtyDays = 'PAGEVIEWS_PER_VISIT_LAST_60_DAYS',
    BouncedVisitsLastDay = 'BOUNCED_VISITS_LAST_DAY',
    BouncedVisitsLastThreeDays = 'BOUNCED_VISITS_LAST_3_DAYS',
    BouncedVisitsLastSevenDays = 'BOUNCED_VISITS_LAST_7_DAYS',
    BouncedVisitsLastThirtyDays = 'BOUNCED_VISITS_LAST_30_DAYS',
    BouncedVisitsLastSixtyDays = 'BOUNCED_VISITS_LAST_60_DAYS',
    NonBouncedVisitsLastDay = 'NON_BOUNCED_VISITS_LAST_DAY',
    NonBouncedVisitsLastThreeDays = 'NON_BOUNCED_VISITS_LAST_3_DAYS',
    NonBouncedVisitsLastSevenDays = 'NON_BOUNCED_VISITS_LAST_7_DAYS',
    NonBouncedVisitsLastThirtyDays = 'NON_BOUNCED_VISITS_LAST_30_DAYS',
    NonBouncedVisitsLastSixtyDays = 'NON_BOUNCED_VISITS_LAST_60_DAYS',
    BounceRateLastDay = 'BOUNCE_RATE_LAST_DAY',
    BounceRateLastThreeDays = 'BOUNCE_RATE_LAST_3_DAYS',
    BounceRateLastSevenDays = 'BOUNCE_RATE_LAST_7_DAYS',
    BounceRateLastThirtyDays = 'BOUNCE_RATE_LAST_30_DAYS',
    BounceRateLastSixtyDays = 'BOUNCE_RATE_LAST_60_DAYS',
    TotalSecondsLastDay = 'TOTAL_SECONDS_LAST_DAY',
    TotalSecondsLastThreeDays = 'TOTAL_SECONDS_LAST_3_DAYS',
    TotalSecondsLastSevenDays = 'TOTAL_SECONDS_LAST_7_DAYS',
    TotalSecondsLastThirtyDays = 'TOTAL_SECONDS_LAST_30_DAYS',
    TotalSecondsLastSixtyDays = 'TOTAL_SECONDS_LAST_60_DAYS',
    AvgTimeOnSiteLastDay = 'AVG_TIME_ON_SITE_LAST_DAY',
    AvgTimeOnSiteLastThreeDays = 'AVG_TIME_ON_SITE_LAST_3_DAYS',
    AvgTimeOnSiteLastSevenDays = 'AVG_TIME_ON_SITE_LAST_7_DAYS',
    AvgTimeOnSiteLastThirtyDays = 'AVG_TIME_ON_SITE_LAST_30_DAYS',
    AvgTimeOnSiteLastSixtyDays = 'AVG_TIME_ON_SITE_LAST_60_DAYS',
    AvgCostPerVisitLastDay = 'AVG_COST_PER_VISIT_LAST_DAY',
    AvgCostPerVisitLastThreeDays = 'AVG_COST_PER_VISIT_LAST_3_DAYS',
    AvgCostPerVisitLastSevenDays = 'AVG_COST_PER_VISIT_LAST_7_DAYS',
    AvgCostPerVisitLastThirtyDays = 'AVG_COST_PER_VISIT_LAST_30_DAYS',
    AvgCostPerVisitLastSixtyDays = 'AVG_COST_PER_VISIT_LAST_60_DAYS',
    AvgCostPerNewVisitorLastDay = 'AVG_COST_PER_NEW_VISITOR_LAST_DAY',
    AvgCostPerNewVisitorLastThreeDays = 'AVG_COST_PER_NEW_VISITOR_LAST_3_DAYS',
    AvgCostPerNewVisitorLastSevenDays = 'AVG_COST_PER_NEW_VISITOR_LAST_7_DAYS',
    AvgCostPerNewVisitorLastThirtyDays = 'AVG_COST_PER_NEW_VISITOR_LAST_30_DAYS',
    AvgCostPerNewVisitorLastSixtyDays = 'AVG_COST_PER_NEW_VISITOR_LAST_60_DAYS',
    AvgCostPerPageviewLastDay = 'AVG_COST_PER_PAGEVIEW_LAST_DAY',
    AvgCostPerPageviewLastThreeDays = 'AVG_COST_PER_PAGEVIEW_LAST_3_DAYS',
    AvgCostPerPageviewLastSevenDays = 'AVG_COST_PER_PAGEVIEW_LAST_7_DAYS',
    AvgCostPerPageviewLastThirtyDays = 'AVG_COST_PER_PAGEVIEW_LAST_30_DAYS',
    AvgCostPerPageviewLastSixtyDays = 'AVG_COST_PER_PAGEVIEW_LAST_60_DAYS',
    AvgCostPerNonBouncedVisitLastDay = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_DAY',
    AvgCostPerNonBouncedVisitLastThreeDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_3_DAYS',
    AvgCostPerNonBouncedVisitLastSevenDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_7_DAYS',
    AvgCostPerNonBouncedVisitLastThirtyDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_30_DAYS',
    AvgCostPerNonBouncedVisitLastSixtyDays = 'AVG_COST_PER_NON_BOUNCED_VISIT_LAST_60_DAYS',
    AvgCostPerMinuteLastDay = 'AVG_COST_PER_MINUTE_LAST_DAY',
    AvgCostPerMinuteLastThreeDays = 'AVG_COST_PER_MINUTE_LAST_3_DAYS',
    AvgCostPerMinuteLastSevenDays = 'AVG_COST_PER_MINUTE_LAST_7_DAYS',
    AvgCostPerMinuteLastThirtyDays = 'AVG_COST_PER_MINUTE_LAST_30_DAYS',
    AvgCostPerMinuteLastSixtyDays = 'AVG_COST_PER_MINUTE_LAST_60_DAYS',
    AvgCostPerUniqueUserLastDay = 'AVG_COST_PER_UNIQUE_USER_LAST_DAY',
    AvgCostPerUniqueUserLastThreeDays = 'AVG_COST_PER_UNIQUE_USER_LAST_3_DAYS',
    AvgCostPerUniqueUserLastSevenDays = 'AVG_COST_PER_UNIQUE_USER_LAST_7_DAYS',
    AvgCostPerUniqueUserLastThirtyDays = 'AVG_COST_PER_UNIQUE_USER_LAST_30_DAYS',
    AvgCostPerUniqueUserLastSixtyDays = 'AVG_COST_PER_UNIQUE_USER_LAST_60_DAYS',
    ConversionsLastDay = 'CONVERSIONS_LAST_DAY',
    ConversionsLastThreeDays = 'CONVERSIONS_LAST_3_DAYS',
    ConversionsLastSevenDays = 'CONVERSIONS_LAST_7_DAYS',
    ConversionsLastThirtyDays = 'CONVERSIONS_LAST_30_DAYS',
    ConversionsLastSixtyDays = 'CONVERSIONS_LAST_60_DAYS',
    ConversionsViewLastDay = 'CONVERSIONS_VIEW_LAST_DAY',
    ConversionsViewLastThreeDays = 'CONVERSIONS_VIEW_LAST_3_DAYS',
    ConversionsViewLastSevenDays = 'CONVERSIONS_VIEW_LAST_7_DAYS',
    ConversionsViewLastThirtyDays = 'CONVERSIONS_VIEW_LAST_30_DAYS',
    ConversionsViewLastSixtyDays = 'CONVERSIONS_VIEW_LAST_60_DAYS',
    ConversionsTotalLastDay = 'CONVERSIONS_TOTAL_LAST_DAY',
    ConversionsTotalLastThreeDays = 'CONVERSIONS_TOTAL_LAST_3_DAYS',
    ConversionsTotalLastSevenDays = 'CONVERSIONS_TOTAL_LAST_7_DAYS',
    ConversionsTotalLastThirtyDays = 'CONVERSIONS_TOTAL_LAST_30_DAYS',
    ConversionsTotalLastSixtyDays = 'CONVERSIONS_TOTAL_LAST_60_DAYS',
    AvgCostPerConversionLastDay = 'AVG_COST_PER_CONVERSION_LAST_DAY',
    AvgCostPerConversionLastThreeDays = 'AVG_COST_PER_CONVERSION_LAST_3_DAYS',
    AvgCostPerConversionLastSevenDays = 'AVG_COST_PER_CONVERSION_LAST_7_DAYS',
    AvgCostPerConversionLastThirtyDays = 'AVG_COST_PER_CONVERSION_LAST_30_DAYS',
    AvgCostPerConversionLastSixtyDays = 'AVG_COST_PER_CONVERSION_LAST_60_DAYS',
    AvgCostPerConversionViewLastDay = 'AVG_COST_PER_CONVERSION_VIEW_LAST_DAY',
    AvgCostPerConversionViewLastThreeDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_3_DAYS',
    AvgCostPerConversionViewLastSevenDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_7_DAYS',
    AvgCostPerConversionViewLastThirtyDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_30_DAYS',
    AvgCostPerConversionViewLastSixtyDays = 'AVG_COST_PER_CONVERSION_VIEW_LAST_60_DAYS',
    AvgCostPerConversionTotalLastDay = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_DAY',
    AvgCostPerConversionTotalLastThreeDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_3_DAYS',
    AvgCostPerConversionTotalLastSevenDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_7_DAYS',
    AvgCostPerConversionTotalLastThirtyDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_30_DAYS',
    AvgCostPerConversionTotalLastSixtyDays = 'AVG_COST_PER_CONVERSION_TOTAL_LAST_60_DAYS',
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
    AvgCostPerVisit = 'AVG_COST_PER_VISIT',
    AvgCostForNewVisitor = 'AVG_COST_PER_NEW_VISITOR',
    AvgCostPerPageview = 'AVG_COST_PER_PAGEVIEW',
    AvgCostPerNonBouncedVisit = 'AVG_COST_PER_NON_BOUNCED_VISIT',
    AvgCostPerMinute = 'AVG_COST_PER_MINUTE',
    AvgCostPerUniqueUser = 'AVG_COST_PER_UNIQUE_USER',
    Conversions = 'CONVERSIONS',
    ConversionsView = 'CONVERSIONS_VIEW',
    ConversionsTotal = 'CONVERSIONS_TOTAL',
    AvgCostPerConversion = 'AVG_COST_PER_CONVERSION',
    AvgCostPerConversionView = 'AVG_COST_PER_CONVERSION_VIEW',
    AvgCostPerConversionTotal = 'AVG_COST_PER_CONVERSION_TOTAL',
    CampaignBudget = 'CAMPAIGN_BUDGET',
    RemainingCampaignBudget = 'CAMPAIGN_REMAINING_BUDGET',
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
    StartsWith = 'STARTS_WITH',
    EndsWith = 'ENDS_WITH',
}

export enum TimeRange {
    LastDay = 'LAST_DAY',
    LastThreeDays = 'LAST_3_DAYS',
    LastSevenDays = 'LAST_7_DAYS',
    LastThirtyDays = 'LAST_30_DAYS',
    LastSixtyDays = 'LAST_60_DAYS',
    NotApplicable = 'NOT_APPLICABLE',
}

export enum RuleHistoryStatus {
    SUCCESS = 1,
    FAILURE = 2,
}

export enum RuleState {
    ENABLED = 'ENABLED',
    PAUSED = 'PAUSED',
}
