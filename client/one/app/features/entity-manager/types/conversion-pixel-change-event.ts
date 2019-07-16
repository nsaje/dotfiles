import {CampaignGoal} from '../../../core/entities/types/campaign/campaign-goal';

export interface ConversionPixelChangeEvent {
    campaignGoal: CampaignGoal;
    conversionPixelName?: string;
}
