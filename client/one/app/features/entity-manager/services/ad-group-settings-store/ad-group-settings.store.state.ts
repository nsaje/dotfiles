import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {BidModifiersImportErrorState} from './bid-modifiers-import-error-state';
import {BidModifierUploadSummary} from '../../../../core/bid-modifiers/types/bid-modifier-upload-summary';
import {RequestState} from '../../../../shared/types/request-state';
import {Deal} from '../../../../core/deals/types/deal';
import {Source} from '../../../../core/sources/types/source';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {GeolocationsByType} from '../../types/geolocations-by-type';
import {GeolocationType} from '../../../../app.constants';

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
        trackingCode: null,
        bid: null,
        dailyBudget: null,
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
            audience: {},
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
    extras: AdGroupExtras = {
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
        agencyUsesRealtimeAutopilot: false,
    };
    sources: Source[] = [];
    availableDeals: Deal[] = [];
    searchedLocations: Geolocation[] = [];
    selectedIncludedLocationsByType: GeolocationsByType = {
        [GeolocationType.COUNTRY]: [],
        [GeolocationType.REGION]: [],
        [GeolocationType.DMA]: [],
        [GeolocationType.CITY]: [],
        [GeolocationType.ZIP]: [],
    };
    selectedExcludedLocationsByType: GeolocationsByType = {
        [GeolocationType.COUNTRY]: [],
        [GeolocationType.REGION]: [],
        [GeolocationType.DMA]: [],
        [GeolocationType.CITY]: [],
        [GeolocationType.ZIP]: [],
    };
    selectedZipTargetingLocation: Geolocation = null;
    fieldsErrors = new AdGroupSettingsStoreFieldsErrorsState();
    dealsRequests = {
        list: {} as RequestState,
    };
    sourcesRequests = {
        list: {} as RequestState,
    };
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
    };
    bidModifiersImportFile: File = null;
    bidModifiersImportSummary: BidModifierUploadSummary = null;
    bidModifiersImportError: BidModifiersImportErrorState = null;
    bidModifiersRequests = {
        import: {} as RequestState,
        validateFile: {} as RequestState,
    };
    locationsRequests = {
        list: {} as RequestState,
        listCountry: {} as RequestState,
        listRegion: {} as RequestState,
        listDma: {} as RequestState,
        listCity: {} as RequestState,
        listZip: {} as RequestState,
    };
}
