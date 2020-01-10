import {AdGroupState, AdState} from '../../../../app.constants';

export interface CampaignCloneSettings {
    destinationCampaignName: string;
    cloneAdGroups: boolean;
    cloneAds: boolean;
    adGroupStateOverride: AdGroupState | null;
    adStateOverride: AdState | null;
}
