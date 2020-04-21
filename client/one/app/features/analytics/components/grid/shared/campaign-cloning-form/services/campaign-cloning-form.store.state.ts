import {RequestState} from '../../../../../../../shared/types/request-state';
import {CampaignCloneSettings} from '../../../../../../../core/entities/types/campaign/campaign-clone-settings';
import {CampaignCloningRule} from '../campaign-cloning.constants';

export class CampaignCloningFormStoreState {
    campaignCloneSettings: CampaignCloneSettings = {
        destinationCampaignName: null,
        cloneAdGroups: null,
        cloneAds: null,
        adGroupStateOverride: null,
        adStateOverride: null,
    };
    cloneRule: CampaignCloningRule = null;
    requests = {
        clone: {} as RequestState,
    };
}
