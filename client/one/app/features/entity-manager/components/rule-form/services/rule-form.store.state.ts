import {Rule} from '../types/rule';
import {
    Unit,
    RuleActionType,
    RuleNotificationType,
    TimeRange,
    RuleDimension,
} from '../rule-form.constants';

export class RuleFormStoreState {
    rule: Rule = {
        dimension: RuleDimension.AdGroup,
        action: {
            type: RuleActionType.IncreaseBudget,
            value: null,
            unit: Unit.Percentage,
            limit: null,
            frequency: null,
            emailSubject: null,
            emailBody: null,
        },
        conditions: [] = [],
        timeRange: TimeRange.LastThreeDays,
        notification: {
            type: RuleNotificationType.Disable,
            recipients: null,
        },
        name: null,
    };
}
