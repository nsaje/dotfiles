import {FieldErrors} from '../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../shared/types/non-field-errors';

export class RulesStoreFieldsErrorsState {
    id: FieldErrors = [];
    agencyId: FieldErrors = [];
    accountId: FieldErrors = [];
    name: FieldErrors = [];
    entities: FieldErrors = [];
    targetType: FieldErrors = [];
    actionType: FieldErrors = [];
    actionFrequency: FieldErrors = [];
    changeStep: FieldErrors = [];
    changeLimit: FieldErrors = [];
    sendEmailRecipients: FieldErrors = [];
    sendEmailSubject: FieldErrors = [];
    sendEmailBody: FieldErrors = [];
    publisherGroupId: FieldErrors = [];
    window: FieldErrors = [];
    notificationType: FieldErrors = [];
    notificationRecipients: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
