import {FieldErrors} from '../../../../../shared/types/field-errors';
import {RuleConditionError} from '../types/rule-condition-error';

export class RulesEditFormStoreFieldsErrorsState {
    id: FieldErrors = [];
    name: FieldErrors = [];
    targetType: FieldErrors = [];
    actionType: FieldErrors = [];
    actionFrequency: FieldErrors = [];
    changeStep: FieldErrors = [];
    changeLimit: FieldErrors = [];
    publisherGroupId: FieldErrors = [];
    conditions: RuleConditionError[] | string[];
    notificationType: FieldErrors = [];
    notificationRecipients: FieldErrors = [];
}
