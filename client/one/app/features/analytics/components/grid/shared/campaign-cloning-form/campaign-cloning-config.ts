import {AdStateOverrideConfig} from './types/ad-state-override-config';
import {AdGroupStateOverrideConfig} from './types/ad-group-state-override-config';
import {CloneRulesConfig} from './types/clone-rules-config';
import {AdState, AdGroupState} from '../../../../../../app.constants';
import {CampaignCloningRule} from './campaign-cloning.constants';

export const CLONE_RULES_OPTIONS: CloneRulesConfig[] = [
    {
        value: CampaignCloningRule.ADS,
        cloneAdGroups: true,
        cloneAds: true,
        description: 'Clone this campaign, ad groups and ads.',
    },
    {
        value: CampaignCloningRule.ADGROUPS,
        cloneAdGroups: true,
        cloneAds: false,
        description: 'Clone this campaign and ad groups but not its ads.',
    },
    {
        value: CampaignCloningRule.CAMPAIGN,
        cloneAdGroups: false,
        cloneAds: false,
        description:
            'Clone this campaign and its settings but not its ad groups and ads.',
    },
];

export const AD_GROUP_STATE_OVERRIDES_OPTIONS: AdGroupStateOverrideConfig[] = [
    {
        value: null,
        description: 'Cloned ad groups will keep their current state.',
    },
    {
        value: AdGroupState.INACTIVE,
        description: 'All cloned ad groups will be paused.',
    },
    {
        value: AdGroupState.ACTIVE,
        description: 'All cloned ad groups will be enabled.',
    },
];

export const AD_STATE_OVERRIDES_OPTIONS: AdStateOverrideConfig[] = [
    {
        value: null,
        description: 'Cloned ads will keep their current state.',
    },
    {
        value: AdState.INACTIVE,
        description: 'All cloned ads will be paused.',
    },
    {
        value: AdState.ACTIVE,
        description: 'All cloned ads will be enabled.',
    },
];
