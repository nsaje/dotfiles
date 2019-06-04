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
}

export enum Unit {
    Currency = 'CURRENCY',
    Percentage = 'PERCENTAGE',
}

export enum RuleActionMacro {
    AdGroupName = 'AD_GROUP_NAME',
    AdGroupDailyCap = 'AD_GROUP_DAILY_CAP',
    TotalSpendLastDay = 'TOTAL_SPEND_LAST_1_DAY',
}

export enum RuleNotificationType {
    Disable = 'DISABLE',
    EnableOnRuleRun = 'ENABLE_ON_RULE_RULE',
    EnableOnRulePerform = 'ENABLE_ON_RULE_PERFORM',
}

export enum RuleConditionProperty {
    TotalSpend = 'TOTAL_SPEND',
    Impressions = 'IMPRESSIONS',
    Ctr = 'CTR',
    TimeOnSite = 'TIME_ON_SITE',
    CampaignName = 'CAMPAIGN_NAME',
    PrimaryCampaignGoal = 'PRIMARY_CAMPAIGN_GOAL',
    Status = 'STATUS',
    DailyBudget = 'DAILY_BUDGET',
    AbsoluteValue = 'ABSOLUTE_VALUE',
}

export enum RuleConditionOperator {
    LessThan = 'LESS_THAN',
    GreaterThan = 'GREATER_THAN',
    Contains = 'CONTAINS',
    NotContains = 'NOT_CONTAINS',
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
