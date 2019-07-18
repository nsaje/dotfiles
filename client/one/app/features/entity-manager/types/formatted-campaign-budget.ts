import {CampaignBudgetState} from '../../../app.constants';
import {CampaignBudget} from '../../../core/entities/types/campaign/campaign-budget';
import {Omit} from '../../../shared/types/omit';

export interface FormattedCampaignBudget
    extends Omit<CampaignBudget, 'startDate' | 'endDate' | 'createdDt'> {
    startDate: string;
    endDate: string;
    createdDt: string;
}
