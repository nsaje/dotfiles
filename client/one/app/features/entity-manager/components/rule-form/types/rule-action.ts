import {
    RuleActionType,
    Unit,
    RuleActionFrequency,
} from '../rule-form.constants';

export interface RuleAction {
    type?: RuleActionType;
    value?: number;
    unit?: Unit;
    limit?: number;
    frequency?: RuleActionFrequency;
    emailSubject?: string;
    emailBody?: string;
    emailRecipients?: string;
}
