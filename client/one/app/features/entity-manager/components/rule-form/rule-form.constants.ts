export enum EntityType {
    Ad = 'AD',
    AdGroup = 'AD_GROUP',
    Campaign = 'CAMPAIGN',
    Account = 'ACCOUNT',
    AllAccounts = 'ALL_ACCOUNTS',
}

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
    IncreaseBudget = 'INCREASE_BUDGET',
    DecreaseBudget = 'DECREASE_BUDGET',
    SendEmail = 'SEND_EMAIL',
}

export enum RuleActionFrequency {
    Day1 = '1_DAY',
    Days3 = '3_DAYS',
    Days7 = '7_DAYS',
}

export enum Unit {
    Currency = 'CURRENCY',
    Percentage = 'PERCENTAGE',
}

export enum RuleActionMacro {
    AccountName = 'ACCOUNT_NAME',
    CampaignName = 'CAMPAIGN_NAME',
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupDailyCap = 'AD_GROUP_DAILY_CAP',
    TotalSpendLastDay = 'TOTAL_SPEND_LAST_1_DAY',
    TotalSpendLastThreeDays = 'TOTAL_SPEND_LAST_3_DAY',
    TotalSpendLastSevenDays = 'TOTAL_SPEND_LAST_7_DAY',
    TotalSpendLifetime = 'TOTAL_SPEND_LIFETIME',
}

export enum RuleNotificationType {
    Disable = 'DISABLE',
    EnableOnRuleRun = 'ENABLE_ON_RULE_RULE',
    EnableOnRulePerform = 'ENABLE_ON_RULE_PERFORM',
}

export enum RuleConditionProperty {
    TotalSpend = 'TOTAL_SPEND',
    Impressions = 'IMPRESSIONS',
    Clicks = 'CLICKS',
    Ctr = 'CTR',
    Cpc = 'CPC',
    Cpm = 'CPM',

    Visits = 'VISITS',
    UniqueUsers = 'UNIQUE_USERS',
    NewUsers = 'NEW_USERS',
    ReturningUsers = 'RETURNING_USERS',
    ShareOfNewUsers = 'SHARE_OF_NEW_USERS',
    ClickDiscrepancy = 'CLICK_DISCREPANCY',

    AccountName = 'ACCOUNT_NAME',
    AccountCreatedDate = 'ACCOUNT_CREATED_DATE',
    CampaignName = 'CAMPAIGN_NAME',
    CampaignCreatedDate = 'CAMPAIGN_CREATED_DATE',
    CampaignType = 'CAMPAIGN_TYPE',
    CampaignBudget = 'CAMPAIGN_BUDGET',
    AdGroupName = 'ADGROUP_NAME',
    AdGroupCreatedDate = 'ADGROUP_CREATED_DATE',
    DailyBudget = 'DAILY_BUDGET',

    BudgetStartDate = 'BUDGET_START_DATE',
    DaysUntilBudgetEnd = 'DAYS_UNTIL_BUDGET_END',
    BudgetEndDate = 'BUDGET_END_DATE',
    DaysSinceBudgetStart = 'DAYS_SINCE_BUDGET_START',
    RemainingBudget = 'REMAINING_BUDGET',

    FixedValue = 'FIXED_VALUE',
}

export enum RuleConditionPropertyGroup {
    TrafficAcquisition = 'Traffic acquisition',
    AudienceMetrics = 'Audience metrics',
    Settings = 'Settings',
    Budget = 'Budget',
    FixedValue = 'Fixed value',
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

export enum ValueModifierType {
    IncreaseValue = 'INCREASE_VALUE',
    DecreaseValue = 'DECREASE_VALUE',
}
