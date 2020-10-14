import {AdGroupExtras} from '../../core/entities/types/ad-group/ad-group-extras';

export const adGroupExtrasMock: AdGroupExtras = {
    agencyId: null,
    actionIsWaiting: null,
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
        targetEnvironments: [],
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
    bidModifierTypeSummaries: null,
    currentBids: {
        cpc: null,
        cpm: null,
    },
    agencyUsesRealtimeAutopilot: null,
};
