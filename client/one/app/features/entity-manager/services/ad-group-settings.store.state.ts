import {AdGroup} from '../../../core/entities/types/ad-group';

export class AdGroupSettingsStoreState {
    adGroup: AdGroup = {
        id: null,
        state: null,
        archived: null,
    };
}
