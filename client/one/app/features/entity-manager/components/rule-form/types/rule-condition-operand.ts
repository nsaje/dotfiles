import {RuleConditionProperty} from '../rule-form.constants';
import {RuleConditionOperandModifier} from './rule-condition-operand-modifier';

export interface RuleConditionOperand {
    property?: RuleConditionProperty;
    value?: string;
    modifier?: RuleConditionOperandModifier;
}
