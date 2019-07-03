import {RuleConditionOperator} from '../rule-form.constants';
import {RuleConditionOperandConfig} from './rule-condition-operand-config';

export interface RuleConditionConfig {
    firstOperand: RuleConditionOperandConfig;
    availableOperators: RuleConditionOperator[];
    availableSecondOperands: RuleConditionOperandConfig[];
}
