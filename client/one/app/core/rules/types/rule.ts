import {
    RuleTargetType,
    TimeRange,
    RuleActionType,
    RuleActionFrequency,
    RuleState,
} from '../rules.constants';
import {RuleCondition} from './rule-condition';
import {RuleNotificationType} from '../rules.constants';
import {RuleEntities} from './rule-entities';
import {PublisherGroup} from '../../../core/publisher-groups/types/publisher-group';

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
    publisherGroup: PublisherGroup;
    conditions: RuleCondition[];
    window: TimeRange;
    notificationType: RuleNotificationType;
    notificationRecipients: string[];
    state?: RuleState;
    archived?: boolean;
}
