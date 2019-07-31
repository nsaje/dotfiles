import {CampaignTrackingGa} from './campaign-tracking-ga';
import {CampaignTrackingAdobe} from './campaign-tracking-adobe';

export interface CampaignTracking {
    ga?: CampaignTrackingGa;
    adobe?: CampaignTrackingAdobe;
}
