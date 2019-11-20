import {FieldErrors} from '../../../../shared/types/field-errors';
import {CampaignGoalErrors} from '../../types/campaign-goal-errors';
import {CampaignTrackingErrors} from '../../types/campaign-tracking-errors';
import {CampaignBudgetErrors} from '../../types/campaign-budget-errors';
import {DealErrors} from '../../types/deal-errors';

export class CampaignSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    type: FieldErrors = [];
    campaignManager: FieldErrors = [];
    iabCategory: FieldErrors = [];
    language: FieldErrors = [];
    frequencyCapping: FieldErrors[];
    goalsMissing: FieldErrors = [];
    goals: CampaignGoalErrors[] = [];
    tracking: CampaignTrackingErrors = {
        ga: {
            webPropertyId: [],
        },
        adobe: {
            trackingParameter: [],
        },
    };
    budgets: CampaignBudgetErrors[] = [];
    deals: DealErrors[] = [];
}
