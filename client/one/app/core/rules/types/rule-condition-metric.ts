import {RuleConditionOperandType, TimeRange} from '../rules.constants';

export interface RuleConditionMetric {
    type: RuleConditionOperandType;
    window: TimeRange;
    modifier: string;
}
