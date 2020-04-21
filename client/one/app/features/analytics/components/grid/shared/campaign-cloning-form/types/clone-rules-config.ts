import {CampaignCloningRule} from '../campaign-cloning.constants';

export interface CloneRulesConfig {
    value: CampaignCloningRule;
    cloneAdGroups: boolean;
    cloneAds: boolean;
    description: string;
}
