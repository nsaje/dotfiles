import {FieldErrors} from '../../../types/field-errors';
import {NonFieldErrors} from '../../../types/non-field-errors';

export class DealErrors {
    id: FieldErrors = [];
    dealId: FieldErrors = [];
    agencyId: FieldErrors = [];
    accountId: FieldErrors = [];
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
