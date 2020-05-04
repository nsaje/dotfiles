import {FieldErrors} from '../../../../shared/types/field-errors';

export class PublisherGroupsStoreFieldsErrorsState {
    name: FieldErrors = [];
    entries: FieldErrors = [];
    errorsCsvKey: string;
}
