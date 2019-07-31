import {FieldErrors} from '../../../../shared/types/field-errors';
import {CampaignGoalErrors} from '../../types/campaign-goal-errors';
import {CampaignBudgetErrors} from '../../types/campaign-budget-errors';

export class CampaignSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    goalsMissing: FieldErrors = [];
    goals: CampaignGoalErrors[] = [];
    budgets: CampaignBudgetErrors[] = [];
}
