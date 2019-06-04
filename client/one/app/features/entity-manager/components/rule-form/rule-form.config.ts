import {
    RuleDimension,
    RuleActionType,
    Unit,
    RuleActionFrequency,
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
        ],
    },
};
