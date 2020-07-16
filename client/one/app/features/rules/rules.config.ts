import {
    RuleTargetType,
    RuleActionType,
    RuleActionFrequency,
    RuleConditionOperator,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
    TimeRange,
    Macro,
    RuleState,
    RuleNotificationType,
} from '../../core/rules/rules.constants';
import {DataType, Unit} from '../../app.constants';
import {PaginationState} from '../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../shared/components/smart-grid/types/pagination-options';

export const RULE_TARGET_TYPES = [
    {
        label: 'Ad',
        value: RuleTargetType.Ad,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
            RuleActionType.TurnOff,
        ],
    },
    {
        label: 'Ad group',
        value: RuleTargetType.AdGroup,
        availableActions: [
            RuleActionType.IncreaseBid,
            RuleActionType.DecreaseBid,
            RuleActionType.IncreaseDailyBudget,
            RuleActionType.DecreaseDailyBudget,
            RuleActionType.TurnOff,
            RuleActionType.SendEmail,
        ],
    },
    {
        label: 'Ad group / publishers',
        value: RuleTargetType.AdGroupPublisher,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
            RuleActionType.Blacklist,
            RuleActionType.AddToPublisherGroup,
        ],
    },
    {
        label: 'Ad group / devices',
        value: RuleTargetType.AdGroupDevice,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / countries',
        value: RuleTargetType.AdGroupCountry,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / regions',
        value: RuleTargetType.AdGroupRegion,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / DMAs',
        value: RuleTargetType.AdGroupDma,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / operating systems',
        value: RuleTargetType.AdGroupOs,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / environments',
        value: RuleTargetType.AdGroupEnvironment,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
        ],
    },
    {
        label: 'Ad group / media sources',
        value: RuleTargetType.AdGroupSource,
        availableActions: [
            RuleActionType.IncreaseBidModifier,
            RuleActionType.DecreaseBidModifier,
            RuleActionType.TurnOff,
        ],
    },
];

export const RULE_ACTIONS_OPTIONS = {
    [RuleActionType.IncreaseBid]: {
        label: 'Increase bid by',
        type: RuleActionType.IncreaseBid,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Maximum bid',
        limitDescription: 'Bid will not increase past this value.',
    },
    [RuleActionType.DecreaseBid]: {
        label: 'Decrease bid by',
        type: RuleActionType.DecreaseBid,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
        hasValue: true,
        unit: Unit.CurrencySign,
        hasLimit: true,
        limitLabel: 'Minimum bid',
        limitDescription: 'Bid will not decrease past this value.',
    },
    [RuleActionType.IncreaseBidModifier]: {
        label: 'Increase bid modifier by',
        description:
            'The number of percentage points by which the bid will increase or decrease whenever the rule is applied.',
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
        label: 'Decrease bid modifier by',
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
        limitDescription:
            'Bid modifier will not decrease below this value. Please note that while the decrease by value is positive (since the operation itself is subtraction), the minimum bid modifier should be negative if you would like to reduce the bid modifier below 0%.',
    },
    [RuleActionType.IncreaseDailyBudget]: {
        label: 'Increase daily budget by',
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
        label: 'Decrease daily budget by',
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
        label: 'Turn off',
        type: RuleActionType.TurnOff,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
    [RuleActionType.Blacklist]: {
        label: 'Blacklist',
        type: RuleActionType.Blacklist,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
    [RuleActionType.SendEmail]: {
        label: 'Send email',
        type: RuleActionType.SendEmail,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
    [RuleActionType.AddToPublisherGroup]: {
        label: 'Add to publisher group',
        type: RuleActionType.AddToPublisherGroup,
        hasPublisherGroupSelector: true,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
};

export const TIME_RANGES = [
    {
        label: 'Last Day',
        value: TimeRange.LastDay,
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
        label: 'Last 30 days',
        value: TimeRange.LastThirtyDays,
    },
    {
        label: 'Lifetime',
        value: TimeRange.Lifetime,
    },
];

export const RULE_ACTION_FREQUENCY_OPTIONS = {
    [RuleActionFrequency.Day1]: {
        label: 'Every day',
        value: RuleActionFrequency.Day1,
    },
    [RuleActionFrequency.Days3]: {
        label: 'Every 3 days',
        value: RuleActionFrequency.Days3,
    },
    [RuleActionFrequency.Days7]: {
        label: 'Every 7 days',
        value: RuleActionFrequency.Days7,
    },
};

export const RULE_STATE_OPTIONS = {
    [RuleState.ENABLED]: {
        label: 'Enabled',
        value: RuleState.ENABLED,
    },
    [RuleState.PAUSED]: {
        label: 'Paused',
        value: RuleState.PAUSED,
    },
};

export const RULE_NOTIFICATION_OPTIONS = {
    [RuleNotificationType.None]: {
        label: 'Never',
        value: RuleNotificationType.None,
    },
    [RuleNotificationType.OnRuleRun]: {
        label: 'Always',
        value: RuleNotificationType.OnRuleRun,
    },
    [RuleNotificationType.OnRuleActionTriggered]: {
        label: 'When action is performed',
        value: RuleNotificationType.OnRuleActionTriggered,
    },
};

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
    },
    [RuleConditionOperandType.AverageDailyTotalSpend]: {
        type: RuleConditionOperandType.AverageDailyTotalSpend,
        label: 'Avg. daily total spend',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Impressions]: {
        type: RuleConditionOperandType.Impressions,
        label: 'Impressions',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Clicks]: {
        type: RuleConditionOperandType.Clicks,
        label: 'Clicks',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Ctr]: {
        type: RuleConditionOperandType.Ctr,
        label: 'CTR',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Cpc]: {
        type: RuleConditionOperandType.Cpc,
        label: 'Avg. CPC',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Cpm]: {
        type: RuleConditionOperandType.Cpm,
        label: 'Avg. CPM',
        group: RuleConditionOperandGroup.TrafficAcquisition,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Visits]: {
        type: RuleConditionOperandType.Visits,
        label: 'Visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.UniqueUsers]: {
        type: RuleConditionOperandType.UniqueUsers,
        label: 'Unique users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.NewUsers]: {
        type: RuleConditionOperandType.NewUsers,
        label: 'New users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.ReturningUsers]: {
        type: RuleConditionOperandType.ReturningUsers,
        label: 'Returning users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.PercentNewUsers]: {
        type: RuleConditionOperandType.PercentNewUsers,
        label: '% new users',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.ClickDiscrepancy]: {
        type: RuleConditionOperandType.ClickDiscrepancy,
        label: 'Click discrepancy',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Pageviews]: {
        type: RuleConditionOperandType.Pageviews,
        label: 'Pageviews',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.PageviewsPerVisit]: {
        type: RuleConditionOperandType.PageviewsPerVisit,
        label: 'Pageviews per visit',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.BouncedVisits]: {
        type: RuleConditionOperandType.BouncedVisits,
        label: 'Bounced visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.NonBouncedVisits]: {
        type: RuleConditionOperandType.NonBouncedVisits,
        label: 'Non-bounced visits',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.BounceRate]: {
        type: RuleConditionOperandType.BounceRate,
        label: 'Bounce rate',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.TotalSeconds]: {
        type: RuleConditionOperandType.TotalSeconds,
        label: 'Total seconds',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.TimeOnSite]: {
        type: RuleConditionOperandType.TimeOnSite,
        label: 'Time on site',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerConversion]: {
        type: RuleConditionOperandType.AvgCostPerConversion,
        label: 'Avg. cost per conversion - click attribution',
        group: RuleConditionOperandGroup.Conversions,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerConversionView]: {
        type: RuleConditionOperandType.AvgCostPerConversionView,
        label: 'Avg. cost per conversion - view attribution',
        group: RuleConditionOperandGroup.Conversions,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerConversionTotal]: {
        type: RuleConditionOperandType.AvgCostPerConversionTotal,
        label: 'Avg. cost per conversion - total',
        group: RuleConditionOperandGroup.Conversions,
        hasTimeRangeModifier: true,
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
    [RuleConditionOperandType.AccountCreatedDate]: {
        type: RuleConditionOperandType.AccountCreatedDate,
        label: 'Account created date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceAccountCreated]: {
        type: RuleConditionOperandType.DaysSinceAccountCreated,
        label: 'Days since account created',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CampaignName]: {
        type: RuleConditionOperandType.CampaignName,
        label: 'Campaign name',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.CampaignCreatedDate]: {
        type: RuleConditionOperandType.CampaignCreatedDate,
        label: 'Campaign created date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceCampaignCreated]: {
        type: RuleConditionOperandType.DaysSinceCampaignCreated,
        label: 'Days since campaign created',
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
    [RuleConditionOperandType.AdGroupCreatedDate]: {
        type: RuleConditionOperandType.AdGroupCreatedDate,
        label: 'Ad group created date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceAdGroupCreated]: {
        type: RuleConditionOperandType.DaysSinceAdGroupCreated,
        label: 'Days since ad group created',
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
    [RuleConditionOperandType.AdGroupDailyCap]: {
        type: RuleConditionOperandType.AdGroupDailyCap,
        label: 'Ad group daily cap',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Decimal, unit: Unit.Percent},
    },
    [RuleConditionOperandType.AdTitle]: {
        type: RuleConditionOperandType.AdTitle,
        label: 'Ad title',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AdLabel]: {
        type: RuleConditionOperandType.AdLabel,
        label: 'Ad label',
        group: RuleConditionOperandGroup.Settings,
    },
    [RuleConditionOperandType.AdCreatedDate]: {
        type: RuleConditionOperandType.AdCreatedDate,
        label: 'Ad created date',
        group: RuleConditionOperandGroup.Settings,
        valueModifier: {dataType: DataType.Integer, unit: Unit.Day},
    },
    [RuleConditionOperandType.DaysSinceAdCreated]: {
        type: RuleConditionOperandType.DaysSinceAdCreated,
        label: 'Days since ad created',
        group: RuleConditionOperandGroup.Settings,
    },
};

export const RULE_CONDITIONS_OPTIONS = {
    [RuleConditionOperandType.TotalSpend]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TotalSpend
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CampaignBudget
            // ],
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.RemainingCampaignBudget
            // ],
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.AdGroupDailyBudget
            // ],
        ],
    },
    [RuleConditionOperandType.Impressions]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Impressions
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.Clicks]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Clicks],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.AdGroupDailyClickCap
            // ],
        ],
    },
    [RuleConditionOperandType.Ctr]: {
        metric: RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Ctr],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CtrCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.Cpc]: {
        metric: RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Cpc],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CpcCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.Cpm]: {
        metric: RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Cpm],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CpmCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.Visits]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Visits],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.UniqueUsers]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.UniqueUsers
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.NewUsers]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.NewUsers],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.ReturningUsers]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.ReturningUsers
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.PercentNewUsers]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PercentNewUsers
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.PercentNewUsersCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.ClickDiscrepancy]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.ClickDiscrepancy
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
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
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Pageviews],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.PageviewsPerVisit]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.PageviewsPerVisit
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.PageviewsPerVisitCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.BouncedVisits]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.BouncedVisits
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.NonBouncedVisits]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.NonBouncedVisits
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.BounceRate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.BounceRate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Decimal,
                unit: Unit.Percent,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.BounceRateCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.TotalSeconds]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TotalSeconds
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
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
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.TimeOnSite
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Decimal,
                unit: Unit.Second,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.TimeOnSiteCampaignGoal
            // ],
        ],
    },
    [RuleConditionOperandType.AvgCostPerConversion]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversion
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
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
    [RuleConditionOperandType.AvgCostPerConversionView]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversionView
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
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
    [RuleConditionOperandType.AvgCostPerConversionTotal]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversionTotal
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
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
    [RuleConditionOperandType.RemainingCampaignBudget]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.RemainingCampaignBudget
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CampaignBudget
            // ],
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.TotalSpend
            // ],
        ],
    },
    [RuleConditionOperandType.CampaignBudgetMargin]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetMargin
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.Percent,
                fractionSize: 2,
            },
        ],
    },
    [RuleConditionOperandType.CampaignBudgetStartDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetStartDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.CampaignBudgetEndDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetEndDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.DaysSinceCampaignBudgetStart]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignBudgetStart
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.DaysUntilCampaignBudgetEnd]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysUntilCampaignBudgetEnd
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.AccountName]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AccountName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AccountCreatedDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AccountCreatedDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.DaysSinceAccountCreated]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceAccountCreated
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.CampaignName]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.CampaignCreatedDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignCreatedDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.DaysSinceCampaignCreated]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignCreated
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.CampaignManager]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.CampaignManager
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.AccountManager
            // ],
        ],
    },
    [RuleConditionOperandType.AdGroupName]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupName
            ],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AdGroupCreatedDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupCreatedDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.DaysSinceAdGroupCreated]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceAdGroupCreated
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
    [RuleConditionOperandType.AdGroupStartDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupStartDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.AdGroupEndDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupEndDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.AdGroupDailyCap]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyCap
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
                fractionSize: 2,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.AverageDailyTotalSpend
            // ],
        ],
    },
    [RuleConditionOperandType.AdTitle]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.AdTitle],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AdLabel]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.AdLabel],
        availableOperators: [
            RuleConditionOperator.Equals,
            RuleConditionOperator.NotEquals,
            RuleConditionOperator.Contains,
            RuleConditionOperator.NotContains,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.String,
            },
        ],
    },
    [RuleConditionOperandType.AdCreatedDate]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AdCreatedDate
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Date,
            },
            // RULE_CONDITION_OPERANDS_OPTIONS[
            //     RuleConditionOperandType.CurrentDate
            // ],
        ],
    },
    [RuleConditionOperandType.DaysSinceAdCreated]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.DaysSinceAdCreated
            ],
        availableOperators: [
            RuleConditionOperator.LessThan,
            RuleConditionOperator.GreaterThan,
        ],
        availableValueTypes: [
            {
                ...RULE_CONDITION_OPERANDS_OPTIONS[
                    RuleConditionOperandType.AbsoluteValue
                ],
                dataType: DataType.Integer,
            },
        ],
    },
};

export const EMAIL_MACROS = [
    {label: 'Agency ID', value: Macro.AgencyId},
    {label: 'Agency name', value: Macro.AgencyName},
    {label: 'Account ID', value: Macro.AccountId},
    {label: 'Account Name', value: Macro.AccountName},
    {label: 'Campaign ID', value: Macro.CampaignId},
    {label: 'Campaign name', value: Macro.CampaignName},
    {label: 'Ad group ID', value: Macro.AdGroupId},
    {label: 'Ad group name', value: Macro.AdGroupName},
    {label: 'Ad group daily cap', value: Macro.AdGroupDailyCap},
    {label: 'Campaign budget', value: Macro.CampaignBudget},
    {label: 'Total spend (last day)', value: Macro.TotalSpendLastDay},
    {label: 'Total spend (last 3 days)', value: Macro.TotalSpendLastThreeDays},
    {label: 'Total spend (last 7 days)', value: Macro.TotalSpendLastSevenDays},
    {
        label: 'Total spend (last 30 days)',
        value: Macro.TotalSpendLastThirtyDays,
    },
    {label: 'Total spend (lifetime)', value: Macro.TotalSpendLifetime},
    {label: 'Clicks (last day)', value: Macro.ClicksLastDay},
    {label: 'Clicks (last 3 days)', value: Macro.ClicksLastThreeDays},
    {label: 'Clicks (last 7 days)', value: Macro.ClicksLastSevenDays},
    {label: 'Clicks (last 30 days)', value: Macro.ClicksLastThirtyDays},
    {label: 'Clicks (lifetime)', value: Macro.ClicksLifetime},
    {label: 'Impressions (last day)', value: Macro.ImpressionsLastDay},
    {label: 'Impressions (last 3 days)', value: Macro.ImpressionsLastThreeDays},
    {label: 'Impressions (last 7 days)', value: Macro.ImpressionsLastSevenDays},
    {
        label: 'Impressions (last 30 days)',
        value: Macro.ImpressionsLastThirtyDays,
    },
    {label: 'Impressions (lifetime)', value: Macro.ImpressionsLifetime},
    {label: 'Avg. CPC (last day)', value: Macro.AvgCpcLastDay},
    {label: 'Avg. CPC (last 3 days)', value: Macro.AvgCpcLastThreeDays},
    {label: 'Avg. CPC (last 7 days)', value: Macro.AvgCpcLastSevenDays},
    {label: 'Avg. CPC (last 30 days)', value: Macro.AvgCpcLastThirtyDays},
    {label: 'Avg. CPC (lifetime)', value: Macro.AvgCpcLifetime},
    {label: 'Avg. CPM (last day)', value: Macro.AvgCpmLastDay},
    {label: 'Avg. CPM (last 3 days)', value: Macro.AvgCpmLastThreeDays},
    {label: 'Avg. CPM (last 7 days)', value: Macro.AvgCpmLastSevenDays},
    {label: 'Avg. CPM (last 30 days)', value: Macro.AvgCpmLastThirtyDays},
    {label: 'Avg. CPM (lifetime)', value: Macro.AvgCpmLifetime},
    {label: 'Visits (last day)', value: Macro.VisitsLastDay},
    {label: 'Visits (last 3 days)', value: Macro.VisitsLastThreeDays},
    {label: 'Visits (last 7 days)', value: Macro.VisitsLastSevenDays},
    {label: 'Visits (last 30 days)', value: Macro.VisitsLastThirtyDays},
    {label: 'Visits (lifetime)', value: Macro.VisitsLifetime},
    {label: 'Unique users (last day)', value: Macro.UniqueUsersLastDay},
    {
        label: 'Unique users (last 3 days)',
        value: Macro.UniqueUsersLastThreeDays,
    },
    {
        label: 'Unique users (last 7 days)',
        value: Macro.UniqueUsersLastSevenDays,
    },
    {
        label: 'Unique users (last 30 days)',
        value: Macro.UniqueUsersLastThirtyDays,
    },
    {label: 'Unique users (lifetime)', value: Macro.UniqueUsersLifetime},
    {label: 'New users (last day)', value: Macro.NewUsersLastDay},
    {label: 'New users (last 3 days)', value: Macro.NewUsersLastThreeDays},
    {label: 'New users (last 7 days)', value: Macro.NewUsersLastSevenDays},
    {label: 'New users (last 30 days)', value: Macro.NewUsersLastThirtyDays},
    {label: 'New users (lifetime)', value: Macro.NewUsersLifetime},
    {label: 'Returning users (last day)', value: Macro.ReturningUsersLastDay},
    {
        label: 'Returning users (last 3 days)',
        value: Macro.ReturningUsersLastThreeDays,
    },
    {
        label: 'Returning users (last 7 days)',
        value: Macro.ReturningUsersLastSevenDays,
    },
    {
        label: 'Returning users (last 30 days)',
        value: Macro.ReturningUsersLastThirtyDays,
    },
    {
        label: 'Returning users (lifetime)',
        value: Macro.ReturningUsersLifetime,
    },
    {label: '% new users (last day)', value: Macro.PercentNewUsersLastDay},
    {
        label: '% new users (last 3 days)',
        value: Macro.PercentNewUsersLastThreeDays,
    },
    {
        label: '% new users (last 7 days)',
        value: Macro.PercentNewUsersLastSevenDays,
    },
    {
        label: '% new users (last 30 days)',
        value: Macro.PercentNewUsersLastThirtyDays,
    },
    {
        label: '% new users (lifetime)',
        value: Macro.PercentNewUsersLifetime,
    },
    {
        label: 'Click discrepancy (last day)',
        value: Macro.ClickDiscrepancyLastDay,
    },
    {
        label: 'Click discrepancy (last 3 days)',
        value: Macro.ClickDiscrepancyLastThreeDays,
    },
    {
        label: 'Click discrepancy (last 7 days)',
        value: Macro.ClickDiscrepancyLastSevenDays,
    },
    {
        label: 'Click discrepancy (last 30 days)',
        value: Macro.ClickDiscrepancyLastThirtyDays,
    },
    {
        label: 'Click discrepancy (lifetime)',
        value: Macro.ClickDiscrepancyLifetime,
    },
    {label: 'Pageviews (last day)', value: Macro.PageviewsLastDay},
    {label: 'Pageviews (last 3 days)', value: Macro.PageviewsLastThreeDays},
    {label: 'Pageviews (last 7 days)', value: Macro.PageviewsLastSevenDays},
    {label: 'Pageviews (last 30 days)', value: Macro.PageviewsLastThirtyDays},
    {label: 'Pageviews (lifetime)', value: Macro.PageviewsLifetime},
    {
        label: 'Pageviews per visit (last day)',
        value: Macro.PageviewsPerVisitLastDay,
    },
    {
        label: 'Pageviews per visit (last 3 days)',
        value: Macro.PageviewsPerVisitLastThreeDays,
    },
    {
        label: 'Pageviews per visit (last 7 days)',
        value: Macro.PageviewsPerVisitLastSevenDays,
    },
    {
        label: 'Pageviews per visit (last 30 days)',
        value: Macro.PageviewsPerVisitLastThirtyDays,
    },
    {
        label: 'Pageviews per visit (lifetime)',
        value: Macro.PageviewsPerVisitLifetime,
    },
    {label: 'Bounced visits (last day)', value: Macro.BouncedVisitsLastDay},
    {
        label: 'Bounced visits (last 3 days)',
        value: Macro.BouncedVisitsLastThreeDays,
    },
    {
        label: 'Bounced visits (last 7 days)',
        value: Macro.BouncedVisitsLastSevenDays,
    },
    {
        label: 'Bounced visits (last 30 days)',
        value: Macro.BouncedVisitsLastThirtyDays,
    },
    {
        label: 'Bounced visits (lifetime)',
        value: Macro.BouncedVisitsLifetime,
    },
    {
        label: 'Non-bounced visits (last day)',
        value: Macro.NonBouncedVisitsLastDay,
    },
    {
        label: 'Non-bounced visits (last 3 days)',
        value: Macro.NonBouncedVisitsLastThreeDays,
    },
    {
        label: 'Non-bounced visits (last 7 days)',
        value: Macro.NonBouncedVisitsLastSevenDays,
    },
    {
        label: 'Non-bounced visits (last 30 days)',
        value: Macro.NonBouncedVisitsLastThirtyDays,
    },
    {
        label: 'Non-bounced visits (lifetime)',
        value: Macro.NonBouncedVisitsLifetime,
    },
    {label: 'Bounce rate (last day)', value: Macro.BounceRateLastDay},
    {label: 'Bounce rate (last 3 days)', value: Macro.BounceRateLastThreeDays},
    {label: 'Bounce rate (last 7 days)', value: Macro.BounceRateLastSevenDays},
    {
        label: 'Bounce rate (last 30 days)',
        value: Macro.BounceRateLastThirtyDays,
    },
    {label: 'Bounce rate (lifetime)', value: Macro.BounceRateLifetime},
    {label: 'Total seconds (last day)', value: Macro.TotalSecondsLastDay},
    {
        label: 'Total seconds (last 3 days)',
        value: Macro.TotalSecondsLastThreeDays,
    },
    {
        label: 'Total seconds (last 7 days)',
        value: Macro.TotalSecondsLastSevenDays,
    },
    {
        label: 'Total seconds (last 30 days)',
        value: Macro.TotalSecondsLastThirtyDays,
    },
    {
        label: 'Total seconds (lifetime)',
        value: Macro.TotalSecondsLifetime,
    },
    {label: 'Time on site (last day)', value: Macro.AvgTimeOnSiteLastDay},
    {
        label: 'Time on site (last 3 days)',
        value: Macro.AvgTimeOnSiteLastThreeDays,
    },
    {
        label: 'Time on site (last 7 days)',
        value: Macro.AvgTimeOnSiteLastSevenDays,
    },
    {
        label: 'Time on site (last 30 days)',
        value: Macro.AvgTimeOnSiteLastThirtyDays,
    },
    {
        label: 'Time on site (lifetime)',
        value: Macro.AvgTimeOnSiteLifetime,
    },
    {
        label: 'Avg. cost per visit (last day)',
        value: Macro.AvgCostPerVisitLastDay,
    },
    {
        label: 'Avg. cost per visit (last 3 days)',
        value: Macro.AvgCostPerVisitLastThreeDays,
    },
    {
        label: 'Avg. cost per visit (last 7 days)',
        value: Macro.AvgCostPerVisitLastSevenDays,
    },
    {
        label: 'Avg. cost per visit (last 30 days)',
        value: Macro.AvgCostPerVisitLastThirtyDays,
    },
    {
        label: 'Avg. cost per visit (lifetime)',
        value: Macro.AvgCostPerVisitLifetime,
    },
    {
        label: 'Avg. cost per new visitor (last day)',
        value: Macro.AvgCostPerNewVisitorLastDay,
    },
    {
        label: 'Avg. cost per new visitor (last 3 days)',
        value: Macro.AvgCostPerNewVisitorLastThreeDays,
    },
    {
        label: 'Avg. cost per new visitor (last 7 days)',
        value: Macro.AvgCostPerNewVisitorLastSevenDays,
    },
    {
        label: 'Avg. cost per new visitor (last 30 days)',
        value: Macro.AvgCostPerNewVisitorLastThirtyDays,
    },
    {
        label: 'Avg. cost per new visitor (lifetime)',
        value: Macro.AvgCostPerNewVisitorLifetime,
    },
    {
        label: 'Avg. cost per pageview (last day)',
        value: Macro.AvgCostPerPageviewLastDay,
    },
    {
        label: 'Avg. cost per pageview (last 3 days)',
        value: Macro.AvgCostPerPageviewLastThreeDays,
    },
    {
        label: 'Avg. cost per pageview (last 7 days)',
        value: Macro.AvgCostPerPageviewLastSevenDays,
    },
    {
        label: 'Avg. cost per pageview (last 30 days)',
        value: Macro.AvgCostPerPageviewLastThirtyDays,
    },
    {
        label: 'Avg. cost per pageview (lifetime)',
        value: Macro.AvgCostPerPageviewLifetime,
    },
    {
        label: 'Avg. cost per non-bounced visit (last day)',
        value: Macro.AvgCostPerNonBouncedVisitLastDay,
    },
    {
        label: 'Avg. cost per non-bounced visit (last 3 days)',
        value: Macro.AvgCostPerNonBouncedVisitLastThreeDays,
    },
    {
        label: 'Avg. cost per non-bounced visit (last 7 days)',
        value: Macro.AvgCostPerNonBouncedVisitLastSevenDays,
    },
    {
        label: 'Avg. cost per non-bounced visit (last 30 days)',
        value: Macro.AvgCostPerNonBouncedVisitLastThirtyDays,
    },
    {
        label: 'Avg. cost per non-bounced visit (lifetime)',
        value: Macro.AvgCostPerNonBouncedVisitLifetime,
    },
    {
        label: 'Avg. cost per minute (last day)',
        value: Macro.AvgCostPerMinuteLastDay,
    },
    {
        label: 'Avg. cost per minute (last 3 days)',
        value: Macro.AvgCostPerMinuteLastThreeDays,
    },
    {
        label: 'Avg. cost per minute (last 7 days)',
        value: Macro.AvgCostPerMinuteLastSevenDays,
    },
    {
        label: 'Avg. cost per minute (last 30 days)',
        value: Macro.AvgCostPerMinuteLastThirtyDays,
    },
    {
        label: 'Avg. cost per minute (lifetime)',
        value: Macro.AvgCostPerMinuteLifetime,
    },
    {
        label: 'Avg. cost per conversion (last day)',
        value: Macro.AvgCostPerConversionLastDay,
    },
    {
        label: 'Avg. cost per conversion (last 3 days)',
        value: Macro.AvgCostPerConversionLastThreeDays,
    },
    {
        label: 'Avg. cost per conversion (last 7 days)',
        value: Macro.AvgCostPerConversionLastSevenDays,
    },
    {
        label: 'Avg. cost per conversion (last 30 days)',
        value: Macro.AvgCostPerConversionLastThirtyDays,
    },
    {
        label: 'Avg. cost per conversion (lifetime)',
        value: Macro.AvgCostPerConversionLifetime,
    },
    {
        label: 'Avg. cost per conversion - view attribution (last day)',
        value: Macro.AvgCostPerConversionViewLastDay,
    },
    {
        label: 'Avg. cost per conversion - view attribution (last 3 days)',
        value: Macro.AvgCostPerConversionViewLastThreeDays,
    },
    {
        label: 'Avg. cost per conversion - view attribution (last 7 days)',
        value: Macro.AvgCostPerConversionViewLastSevenDays,
    },
    {
        label: 'Avg. cost per conversion - view attribution (last 30 days)',
        value: Macro.AvgCostPerConversionViewLastThirtyDays,
    },
    {
        label: 'Avg. cost per conversion - view attribution (lifetime)',
        value: Macro.AvgCostPerConversionViewLifetime,
    },
    {
        label: 'Avg. cost per conversion - total (last day)',
        value: Macro.AvgCostPerConversionTotalLastDay,
    },
    {
        label: 'Avg. cost per conversion - total (last 3 days)',
        value: Macro.AvgCostPerConversionTotalLastThreeDays,
    },
    {
        label: 'Avg. cost per conversion - total (last 7 days)',
        value: Macro.AvgCostPerConversionTotalLastSevenDays,
    },
    {
        label: 'Avg. cost per conversion - total (last 30 days)',
        value: Macro.AvgCostPerConversionTotalLastThirtyDays,
    },
    {
        label: 'Avg. cost per conversion - total (lifetime)',
        value: Macro.AvgCostPerConversionTotalLifetime,
    },
];

export const PAGINATION_URL_PARAMS = ['page', 'pageSize'];

export const DEFAULT_PAGINATION: PaginationState = {
    page: 1,
    pageSize: 20,
};

export const DEFAULT_PAGINATION_OPTIONS: PaginationOptions = {
    type: 'server',
    pageSizeOptions: [
        {name: '10', value: 10},
        {name: '20', value: 20},
        {name: '50', value: 50},
    ],
    ...DEFAULT_PAGINATION,
};
