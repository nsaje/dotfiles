import {RuleConditionOperator} from '../rules.constants';
import {RuleConditionMetric} from './rule-condition-metric';
import {RuleConditionValue} from './rule-condition-value';

export interface RuleCondition {
    id: string;
    operator: RuleConditionOperator;
    metric: RuleConditionMetric;
    value: RuleConditionValue;
}
