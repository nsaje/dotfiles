import {Hack} from '../common/hack';
import {AdGroupExtrasWarnings} from './ad-group-extras-warnings';
import {AdGroupExtrasAudience} from './ad-group-extras-audience';
import {AdGroupExtrasRetargetableAdGroup} from './ad-group-extras-retargetable-ad-group';
import {AdGroupExtrasDefaultSettings} from './ad-group-extras-default-settings';
import {Currency, CampaignGoalKPI} from '../../../../app.constants';
import {Deal} from '../common/deal';

export interface AdGroupExtras {
    agencyId: string;
    actionIsWaiting: boolean;
    canArchive: boolean;
    canRestore: boolean;
    isCampaignAutopilotEnabled: boolean;
    accountId: string;
    currency: Currency;
    optimizationObjective: CampaignGoalKPI;
    defaultSettings: AdGroupExtrasDefaultSettings;
    retargetableAdGroups: AdGroupExtrasRetargetableAdGroup[];
    audiences: AdGroupExtrasAudience[];
    warnings: AdGroupExtrasWarnings;
    hacks: Hack[];
    deals: Deal[];
}
