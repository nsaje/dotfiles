import {RuleDimension, TimeRange} from '../rule-form.constants';
import {RuleAction} from './rule-action';
import {RuleCondition} from './rule-condition';
import {RuleNotification} from './rule-notification';

export interface Rule {
    name: string;
    dimension: RuleDimension;
    action: RuleAction;
    conditions: RuleCondition[];
    timeRange: TimeRange;
    notification: RuleNotification;
}
