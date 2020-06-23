import {FieldErrors} from '../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../shared/types/non-field-errors';

export class CreditsStoreFieldsErrorsState {
    id: FieldErrors = [];
    accountId: FieldErrors = [];
    agencyId: FieldErrors = [];
    startDate: FieldErrors = [];
    endDate: FieldErrors = [];
    licenseFee: FieldErrors = [];
    serviceFee: FieldErrors = [];
    currency: FieldErrors = [];
    amount: FieldErrors = [];
    comment: FieldErrors = [];
    contractId: FieldErrors = [];
    contractNumber: FieldErrors = [];
    status: FieldErrors = [];
    effectiveMargin: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
