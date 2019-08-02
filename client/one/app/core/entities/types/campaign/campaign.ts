import {CampaignTracking} from './campaign-tracking';
import {CampaignGoal} from './campaign-goal';
import {CampaignBudget} from './campaign-budget';
import {CampaignType, IabCategory, Language} from '../../../../app.constants';

export interface Campaign {
    id: string;
    accountId: string;
    name: string;
    type: CampaignType;
    campaignManager: number;
    iabCategory: IabCategory;
    language: Language;
    frequencyCapping: number;
    autopilot: boolean;
    archived: boolean;
    tracking?: CampaignTracking;
    goals: CampaignGoal[];
    budgets: CampaignBudget[];
}
