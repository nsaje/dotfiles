import {RequestState} from '../../../../shared/types/request-state';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../../../../core/entities/types/campaign/campaign-extras';
import {CampaignSettingsStoreFieldsErrorsState} from './campaign-settings.store.fields-errors-state';
import {CampaignGoalKPI} from '../../../../app.constants';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {ConversionPixelErrors} from '../../types/conversion-pixel-errors';

export class CampaignSettingsStoreState {
    entity: Campaign = {
        id: null,
        accountId: null,
        name: null,
        type: null,
        archived: null,
        goals: [],
        budgets: [],
    };
    extras: CampaignExtras = {
        currency: null,
        goalsDefaults: {
            [CampaignGoalKPI.TIME_ON_SITE]: null,
            [CampaignGoalKPI.MAX_BOUNCE_RATE]: null,
            [CampaignGoalKPI.PAGES_PER_SESSION]: null,
            [CampaignGoalKPI.CPA]: null,
            [CampaignGoalKPI.CPC]: null,
            [CampaignGoalKPI.CPM]: null,
            [CampaignGoalKPI.NEW_UNIQUE_VISITORS]: null,
            [CampaignGoalKPI.CPV]: null,
            [CampaignGoalKPI.CP_NON_BOUNCED_VISIT]: null,
            [CampaignGoalKPI.CP_NEW_VISITOR]: null,
            [CampaignGoalKPI.CP_PAGE_VIEW]: null,
            [CampaignGoalKPI.CPCV]: null,
        },
        budgetsOverview: {
            campaignSpend: null,
            mediaSpend: null,
            dataSpend: null,
            licenseFee: null,
            margin: null,
            availableBudgetsSum: null,
            unallocatedCredit: null,
        },
        budgetsDepleted: [],
        accountCredits: [],
    };
    fieldsErrors = new CampaignSettingsStoreFieldsErrorsState();
    conversionPixelsErrors: ConversionPixelErrors[] = [];
    conversionPixelsRequests: {
        create: RequestState;
        edit: RequestState;
    }[] = [];
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
        list: {} as RequestState,
    };
    conversionPixels: ConversionPixel[] = [];
}
