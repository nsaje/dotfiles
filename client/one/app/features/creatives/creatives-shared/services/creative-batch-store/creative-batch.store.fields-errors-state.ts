import {FieldErrors} from '../../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../../shared/types/non-field-errors';

export class CreativeBatchStoreFieldsErrorsState {
    id: FieldErrors = [];
    agencyId: FieldErrors = [];
    accountId: FieldErrors = [];
    name: FieldErrors = [];
    status: FieldErrors = [];
    tags: FieldErrors = [];
    imageCrop: FieldErrors = [];
    displayUrl: FieldErrors = [];
    brandName: FieldErrors = [];
    description: FieldErrors = [];
    callToAction: FieldErrors = [];
    createdBy: FieldErrors = [];
    createdDt: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
