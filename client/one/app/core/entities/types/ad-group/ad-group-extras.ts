import {Hack} from '../common/hack';
import {AdGroupExtrasWarnings} from './ad-group-extras-warnings';
import {AdGroupExtrasAudience} from './ad-group-extras-audience';
import {AdGroupExtrasRetargetableAdGroup} from './ad-group-extras-retargetable-ad-group';
import {AdGroupExtrasDefaultSettings} from './ad-group-extras-default-settings';

export interface AdGroupExtras {
    actionIsWaiting: boolean;
    canArchive: boolean;
    canRestore: boolean;
    defaultSettings: AdGroupExtrasDefaultSettings;
    retargetableAdgroups: AdGroupExtrasRetargetableAdGroup[];
    audiences: AdGroupExtrasAudience[];
    warnings: AdGroupExtrasWarnings;
    hacks: Hack[];
}
