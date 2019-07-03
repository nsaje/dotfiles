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

export enum Unit {
    None = 'None',
    Currency = 'CURRENCY',
    Percentage = 'PERCENTAGE',
    Date = 'DATE',
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
    Impressions = 'IMPRESSIONS',
    Clicks = 'CLICKS',
    AdGroupDailyClickCap = 'AD_GROUP_DAILY_CLICK_CAP',
    AdGroupStartDate = 'AD_GROUP_START_DATE',
    CampaignBudget = 'CAMPAIGN_BUDGET',
    RemainingCampaignBudget = 'REMAINING_CAMPAIGN_BUDGET',
    AdGroupDailyBudget = 'AD_GROUP_DAILY_BUDGET',
}

export enum RuleConditionOperandGroup {
    TrafficAcquisition = 'Traffic acquisition',
    AudienceMetrics = 'Audience metrics',
    Settings = 'Settings',
    Budget = 'Budget',
    FixedValue = 'Fixed value',
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
