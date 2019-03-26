import {FieldErrors} from './field-errors';

export interface NestedFieldsErrors {
    [key: string]: FieldErrors | NestedFieldsErrors;
}
