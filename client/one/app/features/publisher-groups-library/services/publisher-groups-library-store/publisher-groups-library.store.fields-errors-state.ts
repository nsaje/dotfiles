import {FieldErrors} from '../../../../shared/types/field-errors';

export class PublisherGroupsLibraryStoreFieldsErrorsState {
    name: FieldErrors = [];
    entries: FieldErrors = [];
    errorsCsvKey: string;
}
