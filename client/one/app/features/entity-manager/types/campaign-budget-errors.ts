import {FieldErrors} from '../../../shared/types/field-errors';

export interface CampaignBudgetErrors {
    startDate: FieldErrors;
    endDate: FieldErrors;
    amount: FieldErrors;
    margin: FieldErrors;
    comment: FieldErrors;
    creditId: FieldErrors;
}
