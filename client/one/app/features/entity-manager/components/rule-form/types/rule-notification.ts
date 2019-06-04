import {RuleNotificationType} from '../rule-form.constants';

export interface RuleNotification {
    type?: RuleNotificationType;
    recipients?: string;
}
