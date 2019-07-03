import {Rule} from '../types/rule';
import {RuleActionConfig} from '../types/rule-action-config';
import {RuleConditionConfig} from '../types/rule-condition-config';
import {TimeRange, RuleNotificationPolicy} from '../rule-form.constants';

export class RuleFormStoreState {
    availableActions: RuleActionConfig[] = [];
    availableConditions: RuleConditionConfig[] = [];
    rule: Rule = {
        name: null,
        dimension: null,
        action: {
            type: null,
            frequency: null,
        },
        conditions: [],
        timeRange: TimeRange.Lifetime,
        notification: {
            policy: RuleNotificationPolicy.DisableNotifications,
            recipients: '',
        },
    };
}
