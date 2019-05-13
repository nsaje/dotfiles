import {CampaignGoal} from './campaign-goal';

export interface Campaign {
    id: string;
    goals: CampaignGoal[];
}
