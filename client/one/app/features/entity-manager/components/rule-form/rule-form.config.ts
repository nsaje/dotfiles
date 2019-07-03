import {
    RuleDimension,
    RuleActionType,
    Unit,
    RuleActionFrequency,
    RuleConditionOperator,
    Macro,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
    TimeRange,
} from './rule-form.constants';

export const RULE_DIMENSIONS = [
    {label: 'Ad', value: RuleDimension.Ad},
    {label: 'Ad group', value: RuleDimension.AdGroup},
    {
        label: 'Ad group / publishers',
        value: RuleDimension.AdGroupPublisher,
    },
    {
        label: 'Ad group / devices',
        value: RuleDimension.AdGroupDevice,
    },
    {
        label: 'Ad group / countries',
        value: RuleDimension.AdGroupCountry,
    },
    {
        label: 'Ad group / regions',
        value: RuleDimension.AdGroupRegion,
    },
    {
        label: 'Ad group / DMAs',
        value: RuleDimension.AdGroupDma,
    },
    {
        label: 'Ad group / OS',
        value: RuleDimension.AdGroupOs,
    },
    {
        label: 'Ad group / placements',
        value: RuleDimension.AdGroupPlacement,
    },
    {
        label: 'Ad group / sources',
        value: RuleDimension.AdGroupSource,
    },
];

export const RULE_ACTIONS_OPTIONS = {
    [RuleActionType.IncreaseCpc]: {
        label: 'Increase bid CPC',
        type: RuleActionType.IncreaseCpc,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Maximum bid CPC',
        limitDescription: 'Bid CPC will not increase past this value',
    },
    [RuleActionType.DecreaseCpc]: {
        label: 'Decrease bid CPC',
        type: RuleActionType.DecreaseCpc,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Minimum bid CPC',
        limitDescription: 'Bid CPC will not decrease past this value',
    },
    [RuleActionType.IncreaseCpm]: {
        label: 'Increase bid CPM',
        type: RuleActionType.IncreaseCpm,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Maximum bid CPM',
        limitDescription: 'Bid CPM will not increase past this value',
    },
    [RuleActionType.DecreaseCpm]: {
        label: 'Decrease bid CPM',
        type: RuleActionType.DecreaseCpm,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Minimum bid CPM',
        limitDescription: 'Bid CPM will not decrease past this value',
    },
    [RuleActionType.IncreaseBidModifier]: {
        label: 'Increase bid modifier',
        type: RuleActionType.IncreaseBidModifier,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Percentage,
        hasLimit: true,
        limitLabel: 'Maximum bid modifier',
        limitDescription: 'Bid modifier will not increase past this value',
    },
    [RuleActionType.DecreaseBidModifier]: {
        label: 'Decrease bid modifier',
        type: RuleActionType.DecreaseBidModifier,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Percentage,
        hasLimit: true,
        limitLabel: 'Minimum bid modifier',
        limitDescription: 'Bid modifier will not decrease past this value',
    },
    [RuleActionType.IncreaseDailyBudget]: {
        label: 'Increase daily budget',
        type: RuleActionType.IncreaseDailyBudget,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Maximum daily budget',
        limitDescription: 'Daily budget will not increase past this value',
    },
    [RuleActionType.DecreaseDailyBudget]: {
        label: 'Decrease daily budget',
        type: RuleActionType.DecreaseDailyBudget,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.Currency,
        hasLimit: true,
        limitLabel: 'Minimum daily budget',
        limitDescription: 'Daily budget will not decrease past this value',
    },
    [RuleActionType.TurnOff]: {
        label: 'Turn off / blacklist',
        type: RuleActionType.TurnOff,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
    [RuleActionType.SendEmail]: {
        label: 'Send an email',
        type: RuleActionType.SendEmail,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
};

export const TIME_RANGES = [
    {
        label: 'Yesterday',
        value: TimeRange.Yesterday,
    },
    {
        label: 'Last 3 days',
        value: TimeRange.LastThreeDays,
    },
    {
        label: 'Last 7 days',
        value: TimeRange.LastSevenDays,
    },
    {
        label: 'Lifetime',
        value: TimeRange.Lifetime,
    },
];

export const EMAIL_MACROS = [
    {
        label: 'Account name',
        value: Macro.AccountName,
    },
    {
        label: 'Campaign name',
        value: Macro.CampaignName,
    },
    {
        label: 'Ad group name',
        value: Macro.AdGroupName,
    },
    {
        label: 'Ad group daily cap',
        value: Macro.AdGroupDailyCap,
    },
    {
        label: 'Total spend (last 1 day)',
        value: Macro.TotalSpendLastDay,
    },
    {
        label: 'Total spend (last 3 day)',
        value: Macro.TotalSpendLastThreeDays,
    },
    {
        label: 'Total spend (last 7 day)',
        value: Macro.TotalSpendLastSevenDays,
    },
    {
        label: 'Total spend (lifetime)',
        value: Macro.TotalSpendLifetime,
    },
];

export const RULE_CONDITION_OPERANDS_OPTIONS = {
    [RuleConditionOperandType.AbsoluteValue]: {
        type: RuleConditionOperandType.AbsoluteValue,
        label: 'Absolute value',
        hasValue: true,
    },
    [RuleConditionOperandType.CurrentDate]: {
        type: RuleConditionOperandType.CurrentDate,
        label: 'Current date',
        valueModifier: {unit: Unit.Date},
    },
    [RuleConditionOperandType.TotalSpend]: {
        type: RuleConditionOperandType.TotalSpend,
        label: 'Total spend',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.Impressions]: {
        type: RuleConditionOperandType.Impressions,
        label: 'Impressions',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.Clicks]: {
        type: RuleConditionOperandType.Clicks,
        label: 'Clicks',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.AdGroupDailyClickCap]: {
        type: RuleConditionOperandType.AdGroupDailyClickCap,
        label: 'Ad group daily click cap',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.AdGroupStartDate]: {
        type: RuleConditionOperandType.AdGroupStartDate,
        label: 'Ad group start date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {unit: Unit.Date},
    },
    [RuleConditionOperandType.CampaignBudget]: {
        type: RuleConditionOperandType.CampaignBudget,
        label: 'Campaign budget',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.RemainingCampaignBudget]: {
        type: RuleConditionOperandType.RemainingCampaignBudget,
        label: 'Remaining campaign budget',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {unit: Unit.Percentage},
    },
    [RuleConditionOperandType.AdGroupDailyBudget]: {
        type: RuleConditionOperandType.AdGroupDailyBudget,
        label: 'Ad group daily budget',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {unit: Unit.Percentage},
    },
};

export const RULE_CONDITIONS_OPTIONS = {
    [RuleConditionOperandType.TotalSpend]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TotalSpend
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                unit: Unit.Currency,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudget
            ],
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.RemainingCampaignBudget
            ],
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyBudget
            ],
        ],
    },
    [RuleConditionOperandType.Impressions]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Impressions
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                unit: Unit.None,
                fractionSize: 0,
            },
        ],
    },
    [RuleConditionOperandType.Clicks]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Clicks],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                unit: Unit.None,
                fractionSize: 0,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyClickCap
            ],
        ],
    },
    [RuleConditionOperandType.AdGroupStartDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupStartDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                unit: Unit.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
};
