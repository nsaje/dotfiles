import {FieldErrors} from '../../../../../shared/types/field-errors';
import {RuleConditionsError} from '../types/rule-conditions-error';

export class RulesEditFormStoreFieldsErrorsState {
    id: FieldErrors = [];
    name: FieldErrors = [];
    targetType: FieldErrors = [];
    actionType: FieldErrors = [];
    actionFrequency: FieldErrors = [];
    changeStep: FieldErrors = [];
    changeLimit: FieldErrors = [];
    conditions: RuleConditionsError[] | string[];
    notificationType: FieldErrors = [];
    notificationRecipients: FieldErrors = [];
}
