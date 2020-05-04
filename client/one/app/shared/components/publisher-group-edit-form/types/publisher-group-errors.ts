import {FieldErrors} from '../../../types/field-errors';

export class PublisherGroupErrors {
    name: FieldErrors = [];
    entries: FieldErrors = [];
    errorsCsvKey: string;
}
