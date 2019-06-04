import {RuleConditionOperator} from '../rule-form.constants';
import {RuleConditionOperand} from './rule-condition-operand';

export interface RuleCondition {
    id?: string;
    firstOperand?: RuleConditionOperand;
    operator?: RuleConditionOperator;
    secondOperand?: RuleConditionOperand;
}
