import {CampaignTracking} from './campaign-tracking';
import {CampaignGoal} from './campaign-goal';
import {CampaignBudget} from './campaign-budget';

export interface Campaign {
    id: string;
    accountId: string;
    name: string;
    type: string;
    autopilot: boolean;
    archived: boolean;
    tracking?: CampaignTracking;
    goals: CampaignGoal[];
    budgets: CampaignBudget[];
}
