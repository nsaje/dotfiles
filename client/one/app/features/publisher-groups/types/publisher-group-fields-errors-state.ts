import {FieldErrors} from '../../../shared/types/field-errors';

export class PublisherGroupFieldsErrorsState {
    id: FieldErrors = [];
    accountId: FieldErrors = [];
    agencyId: FieldErrors = [];
    name: FieldErrors = [];
    entries: FieldErrors = [];
    errorsCsvKey: string;
}
