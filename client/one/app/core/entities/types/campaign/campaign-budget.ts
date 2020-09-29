import {CampaignBudgetState} from '../../../../app.constants';

export interface CampaignBudget {
    id: string;
    creditId: string;
    accountId: string;
    state?: CampaignBudgetState;
    startDate: Date;
    endDate: Date;
    amount: string;
    available?: string;
    spend?: string;
    margin: string;
    licenseFee?: string;
    serviceFee?: string;
    comment: string;
    createdDt?: Date;
    createdBy?: string;
    canEditStartDate: boolean;
    canEditEndDate: boolean;
    canEditAmount: boolean;
    allocatedAmount?: string;
    campaignName?: string;
}
