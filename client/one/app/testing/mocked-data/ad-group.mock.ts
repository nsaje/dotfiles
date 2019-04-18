import {AdGroup} from '../../core/entities/types/ad-group/ad-group';

export const adGroupMock: AdGroup = {
    id: null,
    campaignId: null,
    name: null,
    biddingType: null,
    state: null,
    archived: null,
    startDate: null,
    endDate: null,
    redirectPixelUrls: [],
    redirectJavascript: null,
    trackingCode: null,
    maxCpc: null,
    maxCpm: null,
    deliveryType: null,
    clickCappingDailyAdGroupMaxClicks: null,
    dayparting: null,
    targeting: {
        devices: [],
        placements: [],
        os: [],
        browsers: [],
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
    },
    autopilot: {
        state: null,
        dailyBudget: null,
    },
    manageRtbSourcesAsOne: false,
    frequencyCapping: null,
    notes: null,
};
