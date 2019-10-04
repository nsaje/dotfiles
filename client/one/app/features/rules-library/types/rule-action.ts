import {RuleActionType, RuleActionFrequency} from '../rules-library.constants';

export interface RuleAction {
    type: RuleActionType;
    frequency: RuleActionFrequency;
    value?: number;
    limit?: number;
    emailSubject?: string;
    emailBody?: string;
    emailRecipients?: string;
}
