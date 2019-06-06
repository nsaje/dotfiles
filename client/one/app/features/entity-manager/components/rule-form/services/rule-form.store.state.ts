import {Rule} from '../types/rule';
import {
    Unit,
    RuleActionType,
    RuleNotificationType,
    TimeRange,
    RuleDimension,
} from '../rule-form.constants';
import * as ruleFormHelpers from '../helpers/rule-form.helpers';

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
            emailRecipients: null,
        },
        conditions: [] = [
            {
                id: ruleFormHelpers.uuid(),
                firstOperand: {
                    property: null,
                    value: null,
                    modifier: {
                        timeRangeModifier: null,
                        valueModifier: null,
                    },
                },
                operator: null,
                secondOperand: {
                    property: null,
                    value: null,
                    modifier: {
                        timeRangeModifier: null,
                        valueModifier: null,
                    },
                },
            },
        ],
        timeRange: TimeRange.LastThreeDays,
        notification: {
            type: RuleNotificationType.Disable,
            recipients: null,
        },
        name: null,
    };
}
