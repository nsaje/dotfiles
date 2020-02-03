import {FieldErrors} from '../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../shared/types/non-field-errors';

export class DealsLibraryStoreFieldsErrorsState {
    id: FieldErrors = [];
    agencyId: FieldErrors = [];
    accountId: FieldErrors = [];
    dealId: FieldErrors = [];
    description: FieldErrors = [];
    name: FieldErrors = [];
    source: FieldErrors = [];
    floorPrice: FieldErrors = [];
    validFromDate: FieldErrors = [];
    validToDate: FieldErrors = [];
    createdDt: FieldErrors = [];
    modifiedDt: FieldErrors = [];
    createdBy: FieldErrors = [];
    numOfAccounts: FieldErrors = [];
    numOfCampaigns: FieldErrors = [];
    numOfAdgroups: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
