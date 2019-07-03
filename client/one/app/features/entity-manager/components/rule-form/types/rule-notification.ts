import {RuleNotificationPolicy} from '../rule-form.constants';

export interface RuleNotification {
    policy: RuleNotificationPolicy;
    recipients: string;
}
