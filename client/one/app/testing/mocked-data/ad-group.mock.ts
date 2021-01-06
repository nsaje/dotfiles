import {AdGroup} from '../../core/entities/types/ad-group/ad-group';

export const adGroupMock: AdGroup = {
    id: null,
    campaignId: null,
    name: null,
    biddingType: null,
    dailyBudget: null,
    state: null,
    archived: null,
    startDate: null,
    endDate: null,
    trackingCode: null,
    bid: null,
    deliveryType: null,
    clickCappingDailyAdGroupMaxClicks: null,
    dayparting: null,
    deals: [],
    targeting: {
        devices: [],
        environments: [],
        os: [],
        browsers: {
            included: [],
            excluded: [],
        },
        audience: null,
        geo: {
            included: {
                countries: [],
                regions: [],
                dma: [],
                cities: [],
                postalCodes: [],
            },
            excluded: {
                countries: [],
                regions: [],
                dma: [],
                cities: [],
                postalCodes: [],
            },
        },
        interest: {
            included: [],
            excluded: [],
        },
        publisherGroups: {
            included: [],
            excluded: [],
        },
        customAudiences: {
            included: [],
            excluded: [],
        },
        retargetingAdGroups: {
            included: [],
            excluded: [],
        },
        language: {
            matchingEnabled: null,
        },
        connectionTypes: [],
    },
    autopilot: {
        state: null,
        maxBid: null,
    },
    manageRtbSourcesAsOne: false,
    frequencyCapping: null,
    notes: null,
};
