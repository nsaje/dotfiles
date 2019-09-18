import {FieldErrors} from '../../../../shared/types/field-errors';

export class AccountSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    defaultAccountManager: FieldErrors = [];
    defaultSalesRepresentative: FieldErrors = [];
    defaultCsRepresentative: FieldErrors = [];
    obRepresentative: FieldErrors = [];
    accountType: FieldErrors = [];
    agencyId: FieldErrors = [];
    salesforceUrl: FieldErrors = [];
    currency: FieldErrors = [];
    frequencyCapping: FieldErrors = [];
    allowedMediaSources: FieldErrors = [];
    autoAddNewSources: FieldErrors = [];
}
