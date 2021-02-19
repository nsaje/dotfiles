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
import {DataType, Unit, EntityType} from '../../app.constants';
import {PaginationState} from '../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../shared/components/smart-grid/types/pagination-options';

export const RULE_TARGET_TYPES = [
    {
        label: 'Ad group',
        value: RuleTargetType.AdGroup,
        availableActions: [
            {
                type: RuleActionType.IncreaseBid,
                label: 'Increase ad group bid',
            },
            {
                type: RuleActionType.DecreaseBid,
                label: 'Decrease ad group bid',
            },
            {
                type: RuleActionType.IncreaseDailyBudget,
                label: 'Increase ad group daily budget',
            },
            {
                type: RuleActionType.DecreaseDailyBudget,
                label: 'Decrease ad group daily budget',
            },
            {
                type: RuleActionType.TurnOff,
                label: 'Pause ad group',
            },
            {
                type: RuleActionType.SendEmail,
                label: 'Send email',
            },
        ],
    },
    {
        label: 'Ad group / Ad',
        value: RuleTargetType.Ad,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase ad bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease ad bid modifier',
            },
            {
                type: RuleActionType.TurnOff,
                label: 'Pause ad',
            },
        ],
    },
    {
        label: 'Ad group / publishers',
        value: RuleTargetType.AdGroupPublisher,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase publisher bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease publisher bid modifier',
            },
            {
                type: RuleActionType.Blacklist,
                label: 'Blacklist publisher',
            },
            {
                type: RuleActionType.AddToPublisherGroup,
                label: 'Add publisher to publisher group',
            },
        ],
    },
    {
        label: 'Ad group / placements',
        value: RuleTargetType.AdGroupPlacement,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase placement bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease placement bid modifier',
            },
            {
                type: RuleActionType.Blacklist,
                label: 'Blacklist placement',
            },
            {
                type: RuleActionType.AddToPublisherGroup,
                label: 'Add placement to publisher group',
            },
        ],
    },
    {
        label: 'Ad group / devices',
        value: RuleTargetType.AdGroupDevice,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase device bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease device bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / countries',
        value: RuleTargetType.AdGroupCountry,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase country bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease country bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / regions',
        value: RuleTargetType.AdGroupRegion,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase region bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease region bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / DMAs',
        value: RuleTargetType.AdGroupDma,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase DMA bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease DMA bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / operating systems',
        value: RuleTargetType.AdGroupOs,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase operating system bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease operating system bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / environments',
        value: RuleTargetType.AdGroupEnvironment,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase environment bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease environment bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / media sources',
        value: RuleTargetType.AdGroupSource,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase media source bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease media source bid modifier',
            },
            {
                type: RuleActionType.TurnOff,
                label: 'Pause media source',
            },
        ],
    },
    {
        label: 'Ad group / browsers',
        value: RuleTargetType.AdGroupBrowser,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase browser bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease browser bid modifier',
            },
        ],
    },
    {
        label: 'Ad group / connection types',
        value: RuleTargetType.AdGroupConnectionType,
        availableActions: [
            {
                type: RuleActionType.IncreaseBidModifier,
                label: 'Increase connection type bid modifier',
            },
            {
                type: RuleActionType.DecreaseBidModifier,
                label: 'Decrease connection type bid modifier',
            },
        ],
    },
];

export const RULE_ACTIONS_OPTIONS = {
    [RuleActionType.IncreaseBid]: {
        valueLabel: 'Increase bid by',
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
        valueLabel: 'Decrease bid by',
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
        valueLabel: 'Increase bid modifier by',
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
        valueLabel: 'Decrease bid modifier by',
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
        valueLabel: 'Increase daily budget by',
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
        valueLabel: 'Decrease daily budget by',
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
        valueLabel: 'Pause',
        type: RuleActionType.TurnOff,
        frequencies: [] as RuleActionFrequency[],
    },
    [RuleActionType.Blacklist]: {
        valueLabel: 'Blacklist',
        type: RuleActionType.Blacklist,
        frequencies: [] as RuleActionFrequency[],
    },
    [RuleActionType.SendEmail]: {
        valueLabel: 'Send email',
        type: RuleActionType.SendEmail,
        frequencies: [
            RuleActionFrequency.Day1,
            RuleActionFrequency.Days3,
            RuleActionFrequency.Days7,
        ],
    },
    [RuleActionType.AddToPublisherGroup]: {
        valueLabel: 'Add to publisher group',
        type: RuleActionType.AddToPublisherGroup,
        hasPublisherGroupSelector: true,
        frequencies: [] as RuleActionFrequency[],
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
        label: 'Last 60 days',
        value: TimeRange.LastSixtyDays,
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
    [RuleConditionOperandType.AvgCostPerVisit]: {
        type: RuleConditionOperandType.AvgCostPerVisit,
        label: 'Avg. Cost per Visit',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerNewVisitor]: {
        type: RuleConditionOperandType.AvgCostPerNewVisitor,
        label: 'Avg. Cost per New Visitor',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoStart]: {
        type: RuleConditionOperandType.VideoStart,
        label: 'Video Start',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoFirstQuartile]: {
        type: RuleConditionOperandType.VideoFirstQuartile,
        label: 'Video First Quartile',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoMidpoint]: {
        type: RuleConditionOperandType.VideoMidpoint,
        label: 'Video Midpoint',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoThirdQuartile]: {
        type: RuleConditionOperandType.VideoThirdQuartile,
        label: 'Video Third Quartile',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoComplete]: {
        type: RuleConditionOperandType.VideoComplete,
        label: 'Video Complete',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoStartPercent]: {
        type: RuleConditionOperandType.VideoStartPercent,
        label: '% Video Start',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoFirstQuartilePercent]: {
        type: RuleConditionOperandType.VideoFirstQuartilePercent,
        label: '% Video First Quartile',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoMidpointPercent]: {
        type: RuleConditionOperandType.VideoMidpointPercent,
        label: '% Video Midpoint',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoThirdQuartilePercent]: {
        type: RuleConditionOperandType.VideoThirdQuartilePercent,
        label: '% Video Third Quartile',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.VideoCompletePercent]: {
        type: RuleConditionOperandType.VideoCompletePercent,
        label: '% Video Complete',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCpv]: {
        type: RuleConditionOperandType.AvgCpv,
        label: 'Avg. CPV',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCpcv]: {
        type: RuleConditionOperandType.AvgCpcv,
        label: 'Avg. CPCV',
        group: RuleConditionOperandGroup.VideoMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Mrc50Measurable]: {
        type: RuleConditionOperandType.Mrc50Measurable,
        label: 'Measurable Impressions',
        group: RuleConditionOperandGroup.Viewability,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Mrc50Viewable]: {
        type: RuleConditionOperandType.Mrc50Viewable,
        label: 'Viewable Impressions',
        group: RuleConditionOperandGroup.Viewability,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Mrc50MeasurablePercent]: {
        type: RuleConditionOperandType.Mrc50MeasurablePercent,
        label: '% Measurable Impressions',
        group: RuleConditionOperandGroup.Viewability,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Mrc50ViewablePercent]: {
        type: RuleConditionOperandType.Mrc50ViewablePercent,
        label: '% Viewable Impressions',
        group: RuleConditionOperandGroup.Viewability,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Mrc50Vcpm]: {
        type: RuleConditionOperandType.Mrc50Vcpm,
        label: 'Avg. VCPM',
        group: RuleConditionOperandGroup.Viewability,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerPageview]: {
        type: RuleConditionOperandType.AvgCostPerPageview,
        label: 'Avg. Cost per Pageview',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerNonBouncedVisit]: {
        type: RuleConditionOperandType.AvgCostPerNonBouncedVisit,
        label: 'Avg. Cost per Non-Bounced Visit',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerMinute]: {
        type: RuleConditionOperandType.AvgCostPerMinute,
        label: 'Avg. Cost per Minute',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerUniqueUser]: {
        type: RuleConditionOperandType.AvgCostPerUniqueUser,
        label: 'Avg. Cost per Unique User',
        group: RuleConditionOperandGroup.AudienceMetrics,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Conversions]: {
        type: RuleConditionOperandType.Conversions,
        label: 'Conversions',
        group: RuleConditionOperandGroup.Conversions,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.AvgCostPerConversion]: {
        type: RuleConditionOperandType.AvgCostPerConversion,
        label: 'Avg. cost per conversion',
        group: RuleConditionOperandGroup.Conversions,
        hasTimeRangeModifier: true,
    },
    [RuleConditionOperandType.Roas]: {
        type: RuleConditionOperandType.Roas,
        label: 'ROAS',
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
        label: 'Campaign manager email',
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
                dataType: DataType.Decimal,
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
    [RuleConditionOperandType.AvgCostPerVisit]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerVisit
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
    [RuleConditionOperandType.AvgCostPerNewVisitor]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerNewVisitor
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
    [RuleConditionOperandType.AvgCostPerPageview]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerPageview
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
    [RuleConditionOperandType.AvgCostPerNonBouncedVisit]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerNonBouncedVisit
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
    [RuleConditionOperandType.AvgCostPerMinute]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerMinute
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
    [RuleConditionOperandType.AvgCostPerUniqueUser]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.AvgCostPerUniqueUser
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
    [RuleConditionOperandType.VideoStart]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoStart
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
    [RuleConditionOperandType.VideoFirstQuartile]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoFirstQuartile
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
    [RuleConditionOperandType.VideoMidpoint]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoMidpoint
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
    [RuleConditionOperandType.VideoThirdQuartile]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoThirdQuartile
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
    [RuleConditionOperandType.VideoComplete]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoComplete
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
    [RuleConditionOperandType.VideoStartPercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoStartPercent
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
    [RuleConditionOperandType.VideoFirstQuartilePercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoFirstQuartilePercent
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
    [RuleConditionOperandType.VideoMidpointPercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoMidpointPercent
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
    [RuleConditionOperandType.VideoThirdQuartilePercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoThirdQuartilePercent
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
    [RuleConditionOperandType.VideoCompletePercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.VideoCompletePercent
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
    [RuleConditionOperandType.AvgCpv]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.AvgCpv],
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
    [RuleConditionOperandType.AvgCpcv]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.AvgCpcv],
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
    [RuleConditionOperandType.Mrc50Measurable]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Mrc50Measurable
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
    [RuleConditionOperandType.Mrc50Viewable]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Mrc50Viewable
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
    [RuleConditionOperandType.Mrc50MeasurablePercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Mrc50MeasurablePercent
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
    [RuleConditionOperandType.Mrc50ViewablePercent]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Mrc50ViewablePercent
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
    [RuleConditionOperandType.Mrc50Vcpm]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Mrc50Vcpm],
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
    [RuleConditionOperandType.Conversions]: {
        metric:
            RULE_CONDITION_OPERANDS_OPTIONS[
                RuleConditionOperandType.Conversions
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
    [RuleConditionOperandType.Roas]: {
        metric: RULE_CONDITION_OPERANDS_OPTIONS[RuleConditionOperandType.Roas],
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
            RuleConditionOperator.StartsWith,
            RuleConditionOperator.EndsWith,
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
    {label: 'Total spend (last 60 days)', value: Macro.TotalSpendLastSixtyDays},
    {label: 'Clicks (last day)', value: Macro.ClicksLastDay},
    {label: 'Clicks (last 3 days)', value: Macro.ClicksLastThreeDays},
    {label: 'Clicks (last 7 days)', value: Macro.ClicksLastSevenDays},
    {label: 'Clicks (last 30 days)', value: Macro.ClicksLastThirtyDays},
    {label: 'Clicks (last 60 days)', value: Macro.ClicksLastSixtyDays},
    {label: 'Impressions (last day)', value: Macro.ImpressionsLastDay},
    {label: 'Impressions (last 3 days)', value: Macro.ImpressionsLastThreeDays},
    {label: 'Impressions (last 7 days)', value: Macro.ImpressionsLastSevenDays},
    {
        label: 'Impressions (last 30 days)',
        value: Macro.ImpressionsLastThirtyDays,
    },
    {
        label: 'Impressions (last 60 days)',
        value: Macro.ImpressionsLastSixtyDays,
    },
    {label: 'Avg. CPC (last day)', value: Macro.AvgCpcLastDay},
    {label: 'Avg. CPC (last 3 days)', value: Macro.AvgCpcLastThreeDays},
    {label: 'Avg. CPC (last 7 days)', value: Macro.AvgCpcLastSevenDays},
    {label: 'Avg. CPC (last 30 days)', value: Macro.AvgCpcLastThirtyDays},
    {label: 'Avg. CPC (last 60 days)', value: Macro.AvgCpcLastSixtyDays},
    {label: 'Avg. CPM (last day)', value: Macro.AvgCpmLastDay},
    {label: 'Avg. CPM (last 3 days)', value: Macro.AvgCpmLastThreeDays},
    {label: 'Avg. CPM (last 7 days)', value: Macro.AvgCpmLastSevenDays},
    {label: 'Avg. CPM (last 30 days)', value: Macro.AvgCpmLastThirtyDays},
    {label: 'Avg. CPM (last 60 days)', value: Macro.AvgCpmLastSixtyDays},
    {label: 'Visits (last day)', value: Macro.VisitsLastDay},
    {label: 'Visits (last 3 days)', value: Macro.VisitsLastThreeDays},
    {label: 'Visits (last 7 days)', value: Macro.VisitsLastSevenDays},
    {label: 'Visits (last 30 days)', value: Macro.VisitsLastThirtyDays},
    {label: 'Visits (last 60 days)', value: Macro.VisitsLastSixtyDays},
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
    {
        label: 'Unique users (last 60 days)',
        value: Macro.UniqueUsersLastSixtyDays,
    },
    {label: 'New users (last day)', value: Macro.NewUsersLastDay},
    {label: 'New users (last 3 days)', value: Macro.NewUsersLastThreeDays},
    {label: 'New users (last 7 days)', value: Macro.NewUsersLastSevenDays},
    {label: 'New users (last 30 days)', value: Macro.NewUsersLastThirtyDays},
    {label: 'New users (last 60 days)', value: Macro.NewUsersLastSixtyDays},
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
        label: 'Returning users (last 60 days)',
        value: Macro.ReturningUsersLastSixtyDays,
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
        label: '% new users (last 60 days)',
        value: Macro.PercentNewUsersLastSixtyDays,
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
        label: 'Click discrepancy (last 60 days)',
        value: Macro.ClickDiscrepancyLastSixtyDays,
    },
    {label: 'Pageviews (last day)', value: Macro.PageviewsLastDay},
    {label: 'Pageviews (last 3 days)', value: Macro.PageviewsLastThreeDays},
    {label: 'Pageviews (last 7 days)', value: Macro.PageviewsLastSevenDays},
    {label: 'Pageviews (last 30 days)', value: Macro.PageviewsLastThirtyDays},
    {label: 'Pageviews (last 60 days)', value: Macro.PageviewsLastSixtyDays},
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
        label: 'Pageviews per visit (last 60 days)',
        value: Macro.PageviewsPerVisitLastSixtyDays,
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
        label: 'Bounced visits (last 60 days)',
        value: Macro.BouncedVisitsLastSixtyDays,
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
        label: 'Non-bounced visits (last 60 days)',
        value: Macro.NonBouncedVisitsLastSixtyDays,
    },
    {label: 'Bounce rate (last day)', value: Macro.BounceRateLastDay},
    {label: 'Bounce rate (last 3 days)', value: Macro.BounceRateLastThreeDays},
    {label: 'Bounce rate (last 7 days)', value: Macro.BounceRateLastSevenDays},
    {
        label: 'Bounce rate (last 30 days)',
        value: Macro.BounceRateLastThirtyDays,
    },
    {label: 'Bounce rate (last 60 days)', value: Macro.BounceRateLastSixtyDays},
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
        label: 'Total seconds (last 60 days)',
        value: Macro.TotalSecondsLastSixtyDays,
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
        label: 'Time on site (last 60 days)',
        value: Macro.AvgTimeOnSiteLastSixtyDays,
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
        label: 'Avg. cost per visit (last 60 days)',
        value: Macro.AvgCostPerVisitLastSixtyDays,
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
        label: 'Avg. cost per new visitor (last 60 days)',
        value: Macro.AvgCostPerNewVisitorLastSixtyDays,
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
        label: 'Avg. cost per pageview (last 60 days)',
        value: Macro.AvgCostPerPageviewLastSixtyDays,
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
        label: 'Avg. cost per non-bounced visit (last 60 days)',
        value: Macro.AvgCostPerNonBouncedVisitLastSixtyDays,
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
        label: 'Avg. cost per minute (last 60 days)',
        value: Macro.AvgCostPerMinuteLastSixtyDays,
    },
    {
        label: 'Avg. cost per unique user (last day)',
        value: Macro.AvgCostPerUniqueUserLastDay,
    },
    {
        label: 'Avg. cost per unique user (last 3 days)',
        value: Macro.AvgCostPerUniqueUserLastThreeDays,
    },
    {
        label: 'Avg. cost per unique user (last 7 days)',
        value: Macro.AvgCostPerUniqueUserLastSevenDays,
    },
    {
        label: 'Avg. cost per unique user (last 30 days)',
        value: Macro.AvgCostPerUniqueUserLastThirtyDays,
    },
    {
        label: 'Avg. cost per unique user (last 60 days)',
        value: Macro.AvgCostPerUniqueUserLastSixtyDays,
    },
    {label: 'Video Start (last day)', value: Macro.VideoStartLastDay},
    {label: 'Video Start (last 3 days)', value: Macro.VideoStartLastThreeDays},
    {label: 'Video Start (last 7 days)', value: Macro.VideoStartLastSevenDays},
    {
        label: 'Video Start (last 30 days)',
        value: Macro.VideoStartLastThirtyDays,
    },
    {label: 'Video Start (last 60 days)', value: Macro.VideoStartLastSixtyDays},
    {
        label: 'Video First Quartile (last day)',
        value: Macro.VideoFirstQuartileLastDay,
    },
    {
        label: 'Video First Quartile (last 3 days)',
        value: Macro.VideoFirstQuartileLastThreeDays,
    },
    {
        label: 'Video First Quartile (last 7 days)',
        value: Macro.VideoFirstQuartileLastSevenDays,
    },
    {
        label: 'Video First Quartile (last 30 days)',
        value: Macro.VideoFirstQuartileLastThirtyDays,
    },
    {
        label: 'Video First Quartile (last 60 days)',
        value: Macro.VideoFirstQuartileLastSixtyDays,
    },
    {label: 'Video Midpoint (last day)', value: Macro.VideoMidpointLastDay},
    {
        label: 'Video Midpoint (last 3 days)',
        value: Macro.VideoMidpointLastThreeDays,
    },
    {
        label: 'Video Midpoint (last 7 days)',
        value: Macro.VideoMidpointLastSevenDays,
    },
    {
        label: 'Video Midpoint (last 30 days)',
        value: Macro.VideoMidpointLastThirtyDays,
    },
    {
        label: 'Video Midpoint (last 60 days)',
        value: Macro.VideoMidpointLastSixtyDays,
    },
    {
        label: 'Video Third Quartile (last day)',
        value: Macro.VideoThirdQuartileLastDay,
    },
    {
        label: 'Video Third Quartile (last 3 days)',
        value: Macro.VideoThirdQuartileLastThreeDays,
    },
    {
        label: 'Video Third Quartile (last 7 days)',
        value: Macro.VideoThirdQuartileLastSevenDays,
    },
    {
        label: 'Video Third Quartile (last 30 days)',
        value: Macro.VideoThirdQuartileLastThirtyDays,
    },
    {
        label: 'Video Third Quartile (last 60 days)',
        value: Macro.VideoThirdQuartileLastSixtyDays,
    },
    {label: 'Video Complete (last day)', value: Macro.VideoCompleteLastDay},
    {
        label: 'Video Complete (last 3 days)',
        value: Macro.VideoCompleteLastThreeDays,
    },
    {
        label: 'Video Complete (last 7 days)',
        value: Macro.VideoCompleteLastSevenDays,
    },
    {
        label: 'Video Complete (last 30 days)',
        value: Macro.VideoCompleteLastThirtyDays,
    },
    {
        label: 'Video Complete (last 60 days)',
        value: Macro.VideoCompleteLastSixtyDays,
    },
    {label: '% Video Start (last day)', value: Macro.VideoStartPercentLastDay},
    {
        label: '% Video Start (last 3 days)',
        value: Macro.VideoStartPercentLastThreeDays,
    },
    {
        label: '% Video Start (last 7 days)',
        value: Macro.VideoStartPercentLastSevenDays,
    },
    {
        label: '% Video Start (last 30 days)',
        value: Macro.VideoStartPercentLastThirtyDays,
    },
    {
        label: '% Video Start (last 60 days)',
        value: Macro.VideoStartPercentLastSixtyDays,
    },
    {
        label: '% Video First Quartile (last day)',
        value: Macro.VideoFirstQuartilePercentLastDay,
    },
    {
        label: '% Video First Quartile (last 3 days)',
        value: Macro.VideoFirstQuartilePercentLastThreeDays,
    },
    {
        label: '% Video First Quartile (last 7 days)',
        value: Macro.VideoFirstQuartilePercentLastSevenDays,
    },
    {
        label: '% Video First Quartile (last 30 days)',
        value: Macro.VideoFirstQuartilePercentLastThirtyDays,
    },
    {
        label: '% Video First Quartile (last 60 days)',
        value: Macro.VideoFirstQuartilePercentLastSixtyDays,
    },
    {
        label: '% Video Midpoint (last day)',
        value: Macro.VideoMidpointPercentLastDay,
    },
    {
        label: '% Video Midpoint (last 3 days)',
        value: Macro.VideoMidpointPercentLastThreeDays,
    },
    {
        label: '% Video Midpoint (last 7 days)',
        value: Macro.VideoMidpointPercentLastSevenDays,
    },
    {
        label: '% Video Midpoint (last 30 days)',
        value: Macro.VideoMidpointPercentLastThirtyDays,
    },
    {
        label: '% Video Midpoint (last 60 days)',
        value: Macro.VideoMidpointPercentLastSixtyDays,
    },
    {
        label: '% Video Third Quartile (last day)',
        value: Macro.VideoThirdQuartilePercentLastDay,
    },
    {
        label: '% Video Third Quartile (last 3 days)',
        value: Macro.VideoThirdQuartilePercentLastThreeDays,
    },
    {
        label: '% Video Third Quartile (last 7 days)',
        value: Macro.VideoThirdQuartilePercentLastSevenDays,
    },
    {
        label: '% Video Third Quartile (last 30 days)',
        value: Macro.VideoThirdQuartilePercentLastThirtyDays,
    },
    {
        label: '% Video Third Quartile (last 60 days)',
        value: Macro.VideoThirdQuartilePercentLastSixtyDays,
    },
    {
        label: '% Video Complete (last day)',
        value: Macro.VideoCompletePercentLastDay,
    },
    {
        label: '% Video Complete (last 3 days)',
        value: Macro.VideoCompletePercentLastThreeDays,
    },
    {
        label: '% Video Complete (last 7 days)',
        value: Macro.VideoCompletePercentLastSevenDays,
    },
    {
        label: '% Video Complete (last 30 days)',
        value: Macro.VideoCompletePercentLastThirtyDays,
    },
    {
        label: '% Video Complete (last 60 days)',
        value: Macro.VideoCompletePercentLastSixtyDays,
    },
    {label: 'Avg. CPV (last day)', value: Macro.AvgCpvLastDay},
    {label: 'Avg. CPV (last 3 days)', value: Macro.AvgCpvLastThreeDays},
    {label: 'Avg. CPV (last 7 days)', value: Macro.AvgCpvLastSevenDays},
    {label: 'Avg. CPV (last 30 days)', value: Macro.AvgCpvLastThirtyDays},
    {label: 'Avg. CPV (last 60 days)', value: Macro.AvgCpvLastSixtyDays},
    {label: 'Avg. CPCV (last day)', value: Macro.AvgCpcvLastDay},
    {label: 'Avg. CPCV (last 3 days)', value: Macro.AvgCpcvLastThreeDays},
    {label: 'Avg. CPCV (last 7 days)', value: Macro.AvgCpcvLastSevenDays},
    {label: 'Avg. CPCV (last 30 days)', value: Macro.AvgCpcvLastThirtyDays},
    {label: 'Avg. CPCV (last 60 days)', value: Macro.AvgCpcvLastSixtyDays},
    {
        label: 'Measurable Impressions (last day)',
        value: Macro.Mrc50MeasurableLastDay,
    },
    {
        label: 'Measurable Impressions (last 3 days)',
        value: Macro.Mrc50MeasurableLastThreeDays,
    },
    {
        label: 'Measurable Impressions (last 7 days)',
        value: Macro.Mrc50MeasurableLastSevenDays,
    },
    {
        label: 'Measurable Impressions (last 30 days)',
        value: Macro.Mrc50MeasurableLastThirtyDays,
    },
    {
        label: 'Measurable Impressions (last 60 days)',
        value: Macro.Mrc50MeasurableLastSixtyDays,
    },
    {
        label: 'Viewable Impressions (last day)',
        value: Macro.Mrc50ViewableLastDay,
    },
    {
        label: 'Viewable Impressions (last 3 days)',
        value: Macro.Mrc50ViewableLastThreeDays,
    },
    {
        label: 'Viewable Impressions (last 7 days)',
        value: Macro.Mrc50ViewableLastSevenDays,
    },
    {
        label: 'Viewable Impressions (last 30 days)',
        value: Macro.Mrc50ViewableLastThirtyDays,
    },
    {
        label: 'Viewable Impressions (last 60 days)',
        value: Macro.Mrc50ViewableLastSixtyDays,
    },
    {
        label: '% Measurable Impressions (last day)',
        value: Macro.Mrc50MeasurablePercentLastDay,
    },
    {
        label: '% Measurable Impressions (last 3 days)',
        value: Macro.Mrc50MeasurablePercentLastThreeDays,
    },
    {
        label: '% Measurable Impressions (last 7 days)',
        value: Macro.Mrc50MeasurablePercentLastSevenDays,
    },
    {
        label: '% Measurable Impressions (last 30 days)',
        value: Macro.Mrc50MeasurablePercentLastThirtyDays,
    },
    {
        label: '% Measurable Impressions (last 60 days)',
        value: Macro.Mrc50MeasurablePercentLastSixtyDays,
    },
    {
        label: '% Viewable Impressions (last day)',
        value: Macro.Mrc50ViewablePercentLastDay,
    },
    {
        label: '% Viewable Impressions (last 3 days)',
        value: Macro.Mrc50ViewablePercentLastThreeDays,
    },
    {
        label: '% Viewable Impressions (last 7 days)',
        value: Macro.Mrc50ViewablePercentLastSevenDays,
    },
    {
        label: '% Viewable Impressions (last 30 days)',
        value: Macro.Mrc50ViewablePercentLastThirtyDays,
    },
    {
        label: '% Viewable Impressions (last 60 days)',
        value: Macro.Mrc50ViewablePercentLastSixtyDays,
    },
    {label: 'Avg. VCPM (last day)', value: Macro.Mrc50VcpmLastDay},
    {label: 'Avg. VCPM (last 3 days)', value: Macro.Mrc50VcpmLastThreeDays},
    {label: 'Avg. VCPM (last 7 days)', value: Macro.Mrc50VcpmLastSevenDays},
    {label: 'Avg. VCPM (last 30 days)', value: Macro.Mrc50VcpmLastThirtyDays},
    {label: 'Avg. VCPM (last 60 days)', value: Macro.Mrc50VcpmLastSixtyDays},
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

export const RULE_CURRENCY_HELP_TEXT =
    'The value is in the same currency as the account the rule runs on';

export const RULE_ACTION_DISABLED_HELP_TEXT =
    'Rule action cannot be changed for an existing rule';

export const RULE_PUBLISHER_TARGET_TEXT =
    'To ensure sufficient data, the rule will only perform this action on publishers with an impression count higher than 1000.';

export const RULE_PLACEMENT_TARGET_TEXT =
    'To ensure sufficient data, the rule will only perform this action on placements with an impression count higher than 1000.';

export const ENTITY_TYPE_TEXT = {
    [EntityType.ACCOUNT]: 'accounts',
    [EntityType.CAMPAIGN]: 'campaigns',
    [EntityType.AD_GROUP]: 'adGroups',
};
