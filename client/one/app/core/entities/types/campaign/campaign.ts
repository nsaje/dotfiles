import {CampaignGoal} from './campaign-goal';

export interface Campaign {
    id: string;
    accountId: string;
    name: string;
    type: string;
    archived: boolean;
    goals: CampaignGoal[];
}
