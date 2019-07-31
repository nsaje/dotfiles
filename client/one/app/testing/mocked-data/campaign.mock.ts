import {Campaign} from '../../core/entities/types/campaign/campaign';

export const campaignMock: Campaign = {
    id: null,
    accountId: null,
    name: null,
    type: null,
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
};
