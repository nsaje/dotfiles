export enum RuleDimension {
    Ad = 'AD',
    AdGroup = 'AD_GROUP',
    AdGroupPublisher = 'AD_GROUP_PUBLISHER',
    AdGroupCountry = 'AD_GROUP_COUNTRY',
    AdGroupRegion = 'AD_GROUP_REGION',
    AdGroupDma = 'AD_GROUP_DMA',
    AdGroupDevice = 'AD_GROUP_DEVICE',
    AdGroupOs = 'AD_GROUP_OS',
    AdGroupPlacement = 'AD_GROUP_PLACEMENT',
    AdGroupSource = 'AD_GROUP_SOURCE',
}

export enum RuleActionType {
    IncreaseCpc = 'INCREASE_CPC',
    DecreaseCpc = 'DECREASE_CPC',
    IncreaseCpm = 'INCREASE_CPM',
    DecreaseCpm = 'DECREASE_CPM',
    IncreaseBidModifier = 'INCREASE_BID_MODIFIER',
    DecreaseBidModifier = 'DECREASE_BID_MODIFIER',
    IncreaseDailyBudget = 'INCREASE_BUDGET',
    DecreaseDailyBudget = 'DECREASE_BUDGET',
    TurnOff = 'TURN_OFF',
    SendEmail = 'SEND_EMAIL',
}

export enum RuleActionFrequency {
    Day1 = '1_DAY',
    Days3 = '3_DAYS',
    Days7 = '7_DAYS',
}

export enum Macro {
    AccountName = 'ACCOUNT_NAME',
    CampaignName = 'CAMPAIGN_NAME',
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupDailyCap = 'AD_GROUP_DAILY_CAP',
    TotalSpendLastDay = 'TOTAL_SPEND_LAST_1_DAY',
    TotalSpendLastThreeDays = 'TOTAL_SPEND_LAST_3_DAYS',
    TotalSpendLastSevenDays = 'TOTAL_SPEND_LAST_7_DAYS',
    TotalSpendLifetime = 'TOTAL_SPEND_LIFETIME',
}

export enum RuleConditionOperandType {
    AbsoluteValue = 'ABSOLUTE_VALUE',
    CurrentDate = 'CURRENT_DATE',
    TotalSpend = 'TOTAL_SPEND',
    AverageDailyTotalSpend = 'AVERAGE_DAILY_TOTAL_SPEND',
    Impressions = 'IMPRESSIONS',
    Clicks = 'CLICKS',
    Ctr = 'CTR',
    Cpc = 'CPC',
    Cpm = 'CPM',
    Visits = 'VISITS',
    UniqueUsers = 'UNIQUE_USERS',
    NewUsers = 'NEW_USERS',
    ReturningUsers = 'RETURNING_USERS',
    PercentNewUsers = 'PERCENT_NEW_USERS',
    ClickDiscrepancy = 'CLICK_DISCREPANCY',
    Pageviews = 'PAGEVIEWS',
    PageviewsPerVisit = 'PAGEVIEWS_PER_VISIT',
    BouncedVisits = 'BOUNCED_VISITS',
    NonBouncedVisits = 'NON_BOUNCED_VISITS',
    BounceRate = 'BOUNCE_RATE',
    TotalSeconds = 'TOTAL_SECONDS',
    TimeOnSite = 'TIME_ON_SITE',
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
    AccountManager = 'ACCOUNT_MANAGER',
    AccountCreationDate = 'ACCOUNT_CREATION_DATE',
    DaysSinceAccountCreation = 'DAYS_SINCE_ACCOUNT_CREATION',
    CampaignName = 'CAMPAIGN_NAME',
    CampaignCreationDate = 'CAMPAIGN_CREATION_DATE',
    DaysSinceCampaignCreation = 'DAYS_SINCE_CAMPAIGN_CREATION',
    CampaignManager = 'CAMPAIGN_MANAGER',
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupCreationDate = 'AD_GROUP_CREATION_DATE',
    DaysSinceAdGroupCreation = 'DAYS_SINCE_AD_GROUP_CREATION',
    AdGroupStartDate = 'AD_GROUP_START_DATE',
    AdGroupEndDate = 'AD_GROUP_END_DATE',
    AdGroupDailyBudget = 'AD_GROUP_DAILY_BUDGET',
    AdGroupDailyClickCap = 'AD_GROUP_DAILY_CLICK_CAP',
    CreativeName = 'CREATIVE_NAME',
    CreativeLabel = 'CREATIVE_LABEL',
    CreativeCreationDate = 'CREATIVE_CREATION_DATE',
    DaysSinceCreativeCreation = 'DAYS_SINCE_CREATIVE_CREATION',
}

export enum RuleConditionOperandGroup {
    TrafficAcquisition = 'Traffic acquisition',
    AudienceMetrics = 'Audience metrics',
    Budget = 'Budget',
    Goals = 'Goals',
    Settings = 'Settings',
}

export enum RuleNotificationPolicy {
    DisableNotifications = 'DISABLE_NOTIFICATIONS',
    NotifyRuleRan = 'NOTIFY_RULE_RAN',
    NotifyActionExecuted = 'NOTIFY_ACTION_EXECUTED',
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
    Yesterday = 'YESTERDAY',
    LastThreeDays = 'LAST_THREE_DAYS',
    LastSevenDays = 'LAST_SEVEN_DAYS',
    Lifetime = 'LIFETIME',
}
