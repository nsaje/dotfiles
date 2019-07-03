import {
    Unit,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
} from '../rule-form.constants';
import {RuleConditionOperandValueModifier} from './rule-condition-operand-value-modifier';

export interface RuleConditionOperandConfig {
    type: RuleConditionOperandType;
    label: string;
    group?: RuleConditionOperandGroup;
    hasValue?: boolean;
    hasTimeRangeModifier?: boolean;
    valueModifier?: RuleConditionOperandValueModifier;
    unit?: Unit;
    fractionSize?: number;
}
