import {AdGroupExtras} from '../../core/entities/types/ad-group/ad-group-extras';

export const adGroupExtrasMock: AdGroupExtras = {
    actionIsWaiting: null,
    canArchive: null,
    canRestore: null,
    isCampaignAutopilotEnabled: false,
    accountId: null,
    currency: null,
    optimizationObjective: null,
    defaultSettings: {
        targetRegions: {
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        },
        exclusionTargetRegions: {
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        },
        targetDevices: [],
        targetOs: [],
        targetPlacements: [],
    },
    retargetableAdGroups: [],
    audiences: [],
    warnings: {
        retargeting: {
            sources: [],
        },
    },
    hacks: [],
    deals: [],
};