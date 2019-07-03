import {RuleActionType, RuleActionFrequency} from '../rule-form.constants';

export interface RuleAction {
    type: RuleActionType;
    frequency: RuleActionFrequency;
    value?: number;
    limit?: number;
    emailSubject?: string;
    emailBody?: string;
    emailRecipients?: string;
}
