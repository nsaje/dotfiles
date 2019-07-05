import {Unit, DataType} from '../rule-form.constants';

export interface RuleConditionOperandValueModifier {
    dataType: DataType;
    unit?: Unit;
}
