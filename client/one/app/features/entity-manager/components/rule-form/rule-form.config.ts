import {
    RuleDimension,
    RuleActionType,
    Unit,
    RuleActionFrequency,
    RuleConditionProperty,
    RuleConditionPropertyGroup,
    RuleConditionOperator,
} from './rule-form.constants';

export const RULE_DIMENSIONS = [
    {name: 'Content Ad', value: RuleDimension.Ad},
    {name: 'Ad group', value: RuleDimension.AdGroup},
    {
        name: 'Ad group / publishers',
        value: RuleDimension.AdGroupPublisher,
    },
    {
        name: 'Ad group / devices',
        value: RuleDimension.AdGroupDevice,
    },
    {
        name: 'Ad group / countries',
        value: RuleDimension.AdGroupCountry,
    },
    {
        name: 'Ad group / regions',
        value: RuleDimension.AdGroupRegion,
    },
    {
        name: 'Ad group / DMAs',
        value: RuleDimension.AdGroupDma,
    },
    {
        name: 'Ad group / OS',
        value: RuleDimension.AdGroupOs,
    },
    {
        name: 'Ad group / placements',
        value: RuleDimension.AdGroupPlacement,
    },
    {
        name: 'Ad group / sources',
        value: RuleDimension.AdGroupSource,
    },
];

export const RULE_ACTIONS = {
    [RuleActionType.IncreaseBudget]: {
        name: 'Increase daily budget',
        type: RuleActionType.IncreaseBudget,
        frequencies: [
            {value: RuleActionFrequency.Day1, name: '24 hours (1 day)'},
            {value: RuleActionFrequency.Days3, name: '72 hours (3 days)'},
            {value: RuleActionFrequency.Days7, name: '168 hours (7 days)'},
        ],
        hasValue: true,
        valueUnits: [
            {value: Unit.Percentage, name: '%'},
            {value: Unit.Currency, name: '$'},
        ],
        limitLabel: 'Maximum daily budget:',
        limitDescription: 'Daily budget will not increase past this value',
        limitUnit: '$',
    },
    [RuleActionType.DecreaseBudget]: {
        name: 'Decrease daily budget',
        type: RuleActionType.DecreaseBudget,
        frequencies: [
            {value: RuleActionFrequency.Day1, name: '24 hours (1 day)'},
            {value: RuleActionFrequency.Days3, name: '72 hours (3 days)'},
            {value: RuleActionFrequency.Days7, name: '168 hours (7 days)'},
        ],
        hasValue: true,
        valueUnits: [
            {value: Unit.Percentage, name: '%'},
            {value: Unit.Currency, name: '$'},
        ],
        limitLabel: 'Minimum daily budget:',
        limitDescription: 'Daily budget will not decrease past this value',
        limitUnit: '$',
    },
    [RuleActionType.SendEmail]: {
        name: 'Send an email',
        type: RuleActionType.SendEmail,
        frequencies: [
            {value: RuleActionFrequency.Day1, name: '24 hours (1 day)'},
            {value: RuleActionFrequency.Days3, name: '72 hours (3 days)'},
            {value: RuleActionFrequency.Days7, name: '168 hours (7 days)'},
        ],
    },
};

export const RULE_CONDITION_PROPERTIES = [
    // TrafficAcquisition
    {
        name: 'Total spend',
        value: RuleConditionProperty.TotalSpend,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [
            RuleConditionProperty.FixedValue,
            RuleConditionProperty.DailyBudget,
        ],
    },
    {
        name: 'Impressions',
        value: RuleConditionProperty.Impressions,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Clicks',
        value: RuleConditionProperty.Clicks,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'CTR',
        value: RuleConditionProperty.Ctr,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'CPC',
        value: RuleConditionProperty.Cpc,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'CPM',
        value: RuleConditionProperty.Cpm,
        group: RuleConditionPropertyGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    // AudienceMetrics
    {
        name: 'Visits',
        value: RuleConditionProperty.Visits,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Unique users',
        value: RuleConditionProperty.UniqueUsers,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'New users',
        value: RuleConditionProperty.NewUsers,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Returning users',
        value: RuleConditionProperty.ReturningUsers,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: '% of new users',
        value: RuleConditionProperty.ShareOfNewUsers,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Click discrepancy',
        value: RuleConditionProperty.ClickDiscrepancy,
        group: RuleConditionPropertyGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    // Settings
    {
        name: 'Account name',
        value: RuleConditionProperty.AccountName,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'contains',
                value: RuleConditionOperator.Contains,
            },
            {
                name: 'not contains',
                value: RuleConditionOperator.NotContains,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Account created date',
        value: RuleConditionProperty.AccountCreatedDate,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Campaign name',
        value: RuleConditionProperty.CampaignName,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'contains',
                value: RuleConditionOperator.Contains,
            },
            {
                name: 'not contains',
                value: RuleConditionOperator.NotContains,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Campaign created date',
        value: RuleConditionProperty.CampaignCreatedDate,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Campaign type',
        value: RuleConditionProperty.CampaignType,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'contains',
                value: RuleConditionOperator.Contains,
            },
            {
                name: 'not contains',
                value: RuleConditionOperator.NotContains,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Ad group name',
        value: RuleConditionProperty.AdGroupName,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'contains',
                value: RuleConditionOperator.Contains,
            },
            {
                name: 'not contains',
                value: RuleConditionOperator.NotContains,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Ad group created date',
        value: RuleConditionProperty.AdGroupCreatedDate,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Daily budget',
        value: RuleConditionProperty.DailyBudget,
        group: RuleConditionPropertyGroup.Settings,
        hasTimeRangeModifier: false,
        hasValueModifier: true,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    // Budget
    {
        name: 'Budget start date',
        value: RuleConditionProperty.BudgetStartDate,
        group: RuleConditionPropertyGroup.Budget,
        hasTimeRangeModifier: false,
        hasValueModifier: true,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Days until budget end',
        value: RuleConditionProperty.DaysUntilBudgetEnd,
        group: RuleConditionPropertyGroup.Budget,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Budget end date',
        value: RuleConditionProperty.BudgetEndDate,
        group: RuleConditionPropertyGroup.Budget,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
    {
        name: 'Days since budget start',
        value: RuleConditionProperty.DaysSinceBudgetStart,
        group: RuleConditionPropertyGroup.Budget,
        hasTimeRangeModifier: false,
        hasValueModifier: false,
        operators: [
            {
                name: 'is less than',
                value: RuleConditionOperator.LessThan,
            },
            {
                name: 'is greater Than',
                value: RuleConditionOperator.GreaterThan,
            },
            {
                name: 'equals',
                value: RuleConditionOperator.Equals,
            },
            {
                name: 'not equals',
                value: RuleConditionOperator.NotEquals,
            },
        ],
        rightOperandProperties: [RuleConditionProperty.FixedValue],
    },
];
