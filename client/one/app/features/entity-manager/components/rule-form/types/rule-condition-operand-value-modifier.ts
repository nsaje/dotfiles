import {DataType, Unit} from '../../../../../app.constants';

export interface RuleConditionOperandValueModifier {
    dataType: DataType;
    unit?: Unit;
}
