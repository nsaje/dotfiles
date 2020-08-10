import {FieldErrors} from '../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../shared/types/non-field-errors';

export class UsersStoreFieldsErrorsState {
    email: FieldErrors = [];
    firstName: FieldErrors = [];
    lastName: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
