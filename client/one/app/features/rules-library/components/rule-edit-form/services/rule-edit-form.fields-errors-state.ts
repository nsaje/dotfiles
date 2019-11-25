import {FieldErrors} from '../../../../../shared/types/field-errors';

export class RulesEditFormStoreFieldsErrorsState {
    id: FieldErrors = [];
    name: FieldErrors[];
    dimension: FieldErrors = [];
    actionType: FieldErrors = [];
    actionFrequency: FieldErrors = [];
    conditions: FieldErrors = [];
    notificationType: FieldErrors = [];
    notificationRecipients: FieldErrors = [];
}
