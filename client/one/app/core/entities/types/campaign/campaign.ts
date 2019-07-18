import {CampaignGoal} from './campaign-goal';
import {CampaignBudget} from './campaign-budget';

export interface Campaign {
    id: string;
    accountId: string;
    name: string;
    type: string;
    archived: boolean;
    goals: CampaignGoal[];
    budgets: CampaignBudget[];
}
