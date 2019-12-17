import {FieldErrors} from '../../../../../shared/types/field-errors';

export class RulesEditFormStoreFieldsErrorsState {
    id: FieldErrors = [];
    name: FieldErrors = [];
    targetType: FieldErrors = [];
    actionType: FieldErrors = [];
    actionFrequency: FieldErrors = [];
    changeStep: FieldErrors = [];
    changeLimit: FieldErrors = [];
    conditions: FieldErrors = [];
    notificationType: FieldErrors = [];
    notificationRecipients: FieldErrors = [];
}
