import {RuleConditionOperandType, TimeRange} from '../rules.constants';

export interface RuleConditionValue {
    type: RuleConditionOperandType;
    window: TimeRange;
    value: string;
}
