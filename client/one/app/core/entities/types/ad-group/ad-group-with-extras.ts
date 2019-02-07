import {AdGroup} from './ad-group';
import {AdGroupExtras} from './ad-group-extras';

export interface AdGroupWithExtras {
    adGroup: AdGroup;
    extras: AdGroupExtras;
}
