import {Hack} from '../common/hack';
import {AdGroupExtrasWarnings} from './ad-group-extras-warnings';
import {AdGroupExtrasAudience} from './ad-group-extras-audience';
import {AdGroupExtrasRetargetableAdGroup} from './ad-group-extras-retargetable-ad-group';
import {AdGroupExtrasDefaultSettings} from './ad-group-extras-default-settings';
import {Currency} from '../../../../app.constants';

export interface AdGroupExtras {
    actionIsWaiting: boolean;
    canArchive: boolean;
    canRestore: boolean;
    isCampaignAutopilotEnabled: boolean;
    accountId: number;
    currency: Currency;
    defaultSettings: AdGroupExtrasDefaultSettings;
    retargetableAdGroups: AdGroupExtrasRetargetableAdGroup[];
    audiences: AdGroupExtrasAudience[];
    warnings: AdGroupExtrasWarnings;
    hacks: Hack[];
}
