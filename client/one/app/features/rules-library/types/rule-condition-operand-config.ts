import {
    RuleConditionOperandType,
    RuleConditionOperandGroup,
} from '../rules-library.constants';
import {DataType, Unit} from '../../../app.constants';
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
