import {
    RuleDimension,
    RuleActionType,
    RuleActionFrequency,
    RuleConditionOperator,
    Macro,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
    TimeRange,
} from './rules-library.constants';
import {DataType, Unit} from '../../app.constants';

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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Maximum bid CPC',
        limitDescription: 'Bid CPC will not increase past this value.',
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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Minimum bid CPC',
        limitDescription: 'Bid CPC will not decrease past this value.',
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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Maximum bid CPM',
        limitDescription: 'Bid CPM will not increase past this value.',
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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Minimum bid CPM',
        limitDescription: 'Bid CPM will not decrease past this value.',
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
        unit: Unit.Percent,
        hasLimit: true,
        limitLabel: 'Maximum bid modifier',
        limitDescription: 'Bid modifier will not increase past this value.',
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
        unit: Unit.Percent,
        hasLimit: true,
        limitLabel: 'Minimum bid modifier',
        limitDescription: 'Bid modifier will not decrease past this value.',
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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Maximum daily budget',
        limitDescription: 'Daily budget will not increase past this value.',
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
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Minimum daily budget',
        limitDescription: 'Daily budget will not decrease past this value.',
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
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.TotalSpend]: {
        type: RuleConditionOperandType.TotalSpend,
        label: 'Total spend',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.AverageDailyTotalSpend]: {
        type: RuleConditionOperandType.AverageDailyTotalSpend,
        label: 'Avg. daily total spend',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Impressions]: {
        type: RuleConditionOperandType.Impressions,
        label: 'Impressions',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Clicks]: {
        type: RuleConditionOperandType.Clicks,
        label: 'Clicks',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Ctr]: {
        type: RuleConditionOperandType.Ctr,
        label: 'CTR',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Cpc]: {
        type: RuleConditionOperandType.Cpc,
        label: 'Avg. CPC',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Cpm]: {
        type: RuleConditionOperandType.Cpm,
        label: 'Avg. CPM',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Visits]: {
        type: RuleConditionOperandType.Visits,
        label: 'Visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.UniqueUsers]: {
        type: RuleConditionOperandType.UniqueUsers,
        label: 'Unique users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.NewUsers]: {
        type: RuleConditionOperandType.NewUsers,
        label: 'New users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.ReturningUsers]: {
        type: RuleConditionOperandType.ReturningUsers,
        label: 'Returning users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.PercentNewUsers]: {
        type: RuleConditionOperandType.PercentNewUsers,
        label: '% new users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.ClickDiscrepancy]: {
        type: RuleConditionOperandType.ClickDiscrepancy,
        label: 'Click discrepancy',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.Pageviews]: {
        type: RuleConditionOperandType.Pageviews,
        label: 'Pageviews',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.PageviewsPerVisit]: {
        type: RuleConditionOperandType.PageviewsPerVisit,
        label: 'Pageviews per visit',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.BouncedVisits]: {
        type: RuleConditionOperandType.BouncedVisits,
        label: 'Bounced visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.NonBouncedVisits]: {
        type: RuleConditionOperandType.NonBouncedVisits,
        label: 'Non-bounced visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.BounceRate]: {
        type: RuleConditionOperandType.BounceRate,
        label: 'Bounce rate',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.TotalSeconds]: {
        type: RuleConditionOperandType.TotalSeconds,
        label: 'Total seconds',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.TimeOnSite]: {
        type: RuleConditionOperandType.TimeOnSite,
        label: 'Time on site',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.CampaignBudget]: {
        type: RuleConditionOperandType.CampaignBudget,
        label: 'Campaign budget',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.RemainingCampaignBudget]: {
        type: RuleConditionOperandType.RemainingCampaignBudget,
        label: 'Remaining campaign budget',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.CampaignBudgetMargin]: {
        type: RuleConditionOperandType.CampaignBudgetMargin,
        label: 'Campaign budget margin',
        group: RuleConditionOperandGroup.Budget,
    },
    [RuleConditionOperandType.CampaignBudgetStartDate]: {
        type: RuleConditionOperandType.CampaignBudgetStartDate,
        label: 'Campaign budget start date',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.CampaignBudgetEndDate]: {
        type: RuleConditionOperandType.CampaignBudgetEndDate,
        label: 'Campaign budget end date',
        group: RuleConditionOperandGroup.Budget,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceCampaignBudgetStart]: {
        type: RuleConditionOperandType.DaysSinceCampaignBudgetStart,
        label: 'Days since campaign budget start',
        group: RuleConditionOperandGroup.Budget,
    },
    [RuleConditionOperandType.DaysUntilCampaignBudgetEnd]: {
        type: RuleConditionOperandType.DaysUntilCampaignBudgetEnd,
        label: 'Days until campaign budget end',
        group: RuleConditionOperandGroup.Budget,
    },
    [RuleConditionOperandType.CtrCampaignGoal]: {
        type: RuleConditionOperandType.CtrCampaignGoal,
        label: 'CTR goal',
        group: RuleConditionOperandGroup.Goals,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.CpcCampaignGoal]: {
        type: RuleConditionOperandType.CpcCampaignGoal,
        label: 'CPC goal',
        group: RuleConditionOperandGroup.Goals,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.CpmCampaignGoal]: {
        type: RuleConditionOperandType.CpmCampaignGoal,
        label: 'CPM goal',
        group: RuleConditionOperandGroup.Goals,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.PercentNewUsersCampaignGoal]: {
        type: RuleConditionOperandType.PercentNewUsersCampaignGoal,
        label: 'New users goal',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.PageviewsPerVisitCampaignGoal]: {
        type: RuleConditionOperandType.PageviewsPerVisitCampaignGoal,
        label: 'Pageviews per visit goal',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.BounceRateCampaignGoal]: {
        type: RuleConditionOperandType.BounceRateCampaignGoal,
        label: 'Bounce rate goal',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.TimeOnSiteCampaignGoal]: {
        type: RuleConditionOperandType.TimeOnSiteCampaignGoal,
        label: 'Time on site goal',
        group: RuleConditionOperandGroup.AudienceMetrics,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.AccountName]: {
        type: RuleConditionOperandType.AccountName,
        label: 'Account name',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AccountManager]: {
        type: RuleConditionOperandType.AccountManager,
        label: 'Account manager',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AccountCreationDate]: {
        type: RuleConditionOperandType.AccountCreationDate,
        label: 'Account creation date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceAccountCreation]: {
        type: RuleConditionOperandType.DaysSinceAccountCreation,
        label: 'Days since account creation',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CampaignName]: {
        type: RuleConditionOperandType.CampaignName,
        label: 'Campaign name',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CampaignCreationDate]: {
        type: RuleConditionOperandType.CampaignCreationDate,
        label: 'Campaign creation date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceCampaignCreation]: {
        type: RuleConditionOperandType.DaysSinceCampaignCreation,
        label: 'Days since campaign creation',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CampaignManager]: {
        type: RuleConditionOperandType.CampaignManager,
        label: 'Campaign manager',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AdGroupName]: {
        type: RuleConditionOperandType.AdGroupName,
        label: 'Ad group name',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AdGroupCreationDate]: {
        type: RuleConditionOperandType.AdGroupCreationDate,
        label: 'Ad group creation date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceAdGroupCreation]: {
        type: RuleConditionOperandType.DaysSinceAdGroupCreation,
        label: 'Days since ad group creation',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AdGroupStartDate]: {
        type: RuleConditionOperandType.AdGroupStartDate,
        label: 'Ad group start date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.AdGroupEndDate]: {
        type: RuleConditionOperandType.AdGroupEndDate,
        label: 'Ad group end date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.AdGroupDailyBudget]: {
        type: RuleConditionOperandType.AdGroupDailyBudget,
        label: 'Ad group daily budget',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.AdGroupDailyClickCap]: {
        type: RuleConditionOperandType.AdGroupDailyClickCap,
        label: 'Ad group daily click cap',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.CreativeName]: {
        type: RuleConditionOperandType.CreativeName,
        label: 'Creative name',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CreativeLabel]: {
        type: RuleConditionOperandType.CreativeLabel,
        label: 'Creative label',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CreativeCreationDate]: {
        type: RuleConditionOperandType.CreativeCreationDate,
        label: 'Creative creation date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceCreativeCreation]: {
        type: RuleConditionOperandType.DaysSinceCreativeCreation,
        label: 'Days since creative creation',
        group: RuleConditionOperandGroup.Settings,
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
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
                dataType: DataType.Integer,
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
                dataType: DataType.Integer,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyClickCap
            ],
        ],
    },
    [RuleConditionOperandType.Ctr]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Ctr],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CtrCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.Cpc]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Cpc],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CpcCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.Cpm]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Cpm],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CpmCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.Visits]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Visits],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.UniqueUsers]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.UniqueUsers
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.NewUsers]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.NewUsers],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.ReturningUsers]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.ReturningUsers
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.PercentNewUsers]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PercentNewUsers
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
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PercentNewUsersCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.ClickDiscrepancy]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.ClickDiscrepancy
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
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
        ],
    },
    [RuleConditionOperandType.Pageviews]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Pageviews],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.PageviewsPerVisit]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PageviewsPerVisit
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
                dataType: DataType.Integer,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PageviewsPerVisitCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.BouncedVisits]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.BouncedVisits
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.NonBouncedVisits]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.NonBouncedVisits
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.BounceRate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.BounceRate
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
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.BounceRateCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.TotalSeconds]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TotalSeconds
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
                dataType: DataType.Integer,
                unit: Unit.Second,
            },
        ],
    },
    [RuleConditionOperandType.TimeOnSite]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TimeOnSite
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
                dataType: DataType.Decimal,
                unit: Unit.Second,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TimeOnSiteCampaignGoal
            ],
        ],
    },
    [RuleConditionOperandType.RemainingCampaignBudget]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.RemainingCampaignBudget
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudget
            ],
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TotalSpend
            ],
        ],
    },
    [RuleConditionOperandType.CampaignBudgetMargin]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetMargin
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
        ],
    },
    [RuleConditionOperandType.CampaignBudgetStartDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetStartDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.CampaignBudgetEndDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetEndDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.DaysSinceCampaignBudgetStart]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignBudgetStart
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.DaysUntilCampaignBudgetEnd]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysUntilCampaignBudgetEnd
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.AccountName]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AccountName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AccountCreationDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AccountCreationDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.DaysSinceAccountCreation]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceAccountCreation
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.CampaignName]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.CampaignCreationDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignCreationDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.DaysSinceCampaignCreation]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignCreation
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
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.CampaignManager]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignManager
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AccountManager
            ],
        ],
    },
    [RuleConditionOperandType.AdGroupName]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AdGroupCreationDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupCreationDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.DaysSinceAdGroupCreation]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceAdGroupCreation
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
                dataType: DataType.Integer,
            },
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.AdGroupEndDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupEndDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.AdGroupDailyBudget]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyBudget
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AverageDailyTotalSpend
            ],
        ],
    },
    [RuleConditionOperandType.CreativeName]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CreativeName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.CreativeLabel]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CreativeLabel
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableSecondOperands: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.CreativeCreationDate]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CreativeCreationDate
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
                dataType: DataType.Date,
            },
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CurrentDate
            ],
        ],
    },
    [RuleConditionOperandType.DaysSinceCreativeCreation]: {
        firstOperand:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceCreativeCreation
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
                dataType: DataType.Integer,
            },
        ],
    },
};
