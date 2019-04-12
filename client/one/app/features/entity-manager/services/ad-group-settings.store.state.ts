import {AdGroup} from '../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {RequestState} from 'one/app/shared/types/request-state';

export class AdGroupSettingsStoreState {
    entity: AdGroup = {
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
    extras: AdGroupExtras = {
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
    fieldsErrors = new AdGroupSettingsStoreFieldsErrorsState();
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
    };
}
