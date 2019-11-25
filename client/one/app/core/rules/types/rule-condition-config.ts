import {RuleConditionOperator} from '../rules.constants';
import {RuleConditionOperandConfig} from './rule-condition-operand-config';

export interface RuleConditionConfig {
    metric: RuleConditionOperandConfig;
    availableOperators: RuleConditionOperator[];
    availableValueTypes: RuleConditionOperandConfig[];
}
