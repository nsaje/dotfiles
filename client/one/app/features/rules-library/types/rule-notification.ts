import {RuleNotificationPolicy} from '../rules-library.constants';

export interface RuleNotification {
    policy: RuleNotificationPolicy;
    recipients: string;
}
