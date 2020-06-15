import {
    RuleTargetType,
    TimeRange,
    RuleActionType,
    RuleActionFrequency,
} from '../rules.constants';
import {RuleCondition} from './rule-condition';
import {RuleNotificationType} from '../rules.constants';
import {RuleEntities} from './rule-entities';

export interface Rule {
    id: string;
    agencyId: string | null;
    accountId: string | null;
    name: string;
    entities: RuleEntities;
    targetType: RuleTargetType;
    actionType: RuleActionType;
    actionFrequency: RuleActionFrequency;
    changeStep: number;
    changeLimit: number;
    sendEmailRecipients: string[];
    sendEmailSubject: string;
    sendEmailBody: string;
    publisherGroupId: string;
    conditions: RuleCondition[];
    window: TimeRange;
    notificationType: RuleNotificationType;
    notificationRecipients: string[];
}
