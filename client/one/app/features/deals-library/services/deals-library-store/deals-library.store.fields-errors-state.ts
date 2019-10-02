import {FieldErrors} from '../../../../shared/types/field-errors';

export class DealStoreFieldsErrorsState {
    id: FieldErrors = [];
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
}
