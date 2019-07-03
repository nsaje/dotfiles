import {
    RuleConditionOperator,
    RuleConditionOperandType,
    TimeRange,
} from '../rule-form.constants';

export interface RuleCondition {
    id: string;
    firstOperand: RuleConditionOperandType;
    firstOperandValue: string;
    firstOperandTimeRange: TimeRange;
    operator: RuleConditionOperator;
    secondOperand: RuleConditionOperandType;
    secondOperandValue: string;
    secondOperandTimeRange: TimeRange;
}
