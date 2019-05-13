import {Campaign} from './campaign';
import {CampaignExtras} from './campaign-extras';

export interface CampaignWithExtras {
    campaign: Campaign;
    extras: CampaignExtras;
}
