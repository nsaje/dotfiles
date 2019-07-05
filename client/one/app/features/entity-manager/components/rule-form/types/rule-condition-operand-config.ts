import {
    Unit,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
    DataType,
} from '../rule-form.constants';
import {RuleConditionOperandValueModifier} from './rule-condition-operand-value-modifier';

export interface RuleConditionOperandConfig {
    type: RuleConditionOperandType;
    label: string;
    group?: RuleConditionOperandGroup;
    hasValue?: boolean;
    hasTimeRangeModifier?: boolean;
    valueModifier?: RuleConditionOperandValueModifier;
    dataType?: DataType;
    unit?: Unit;
    fractionSize?: number;
}
