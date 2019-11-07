import {Campaign} from '../../core/entities/types/campaign/campaign';

export const campaignMock: Campaign = {
    id: null,
    accountId: null,
    name: null,
    type: null,
    campaignManager: null,
    iabCategory: null,
    language: null,
    frequencyCapping: null,
    autopilot: null,
    archived: null,
    tracking: {
        ga: {
            enabled: null,
            type: null,
            webPropertyId: null,
        },
        adobe: {
            enabled: null,
            trackingParameter: null,
        },
    },
    goals: [],
    budgets: [],
    targeting: {
        publisherGroups: {
            included: [],
            excluded: [],
        },
    },
    deals: [],
};
