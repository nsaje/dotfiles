import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {BidModifiersImportErrorState} from './bid-modifiers-import-error-state';
import {BidModifierUploadSummary} from '../../../../core/bid-modifiers/types/bid-modifier-upload-summary';
import {RequestState} from '../../../../shared/types/request-state';
import {Deal} from '../../../../core/deals/types/deal';
import {Source} from '../../../../core/sources/types/source';

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
        deals: [],
        targeting: {
            devices: [],
            placements: [],
            os: [],
            browsers: [],
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
        agencyId: null,
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
        bidModifierTypeSummaries: null,
    };
    sources: Source[] = [];
    availableDeals: Deal[] = [];
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
}
