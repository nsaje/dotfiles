import {RequestState} from '../../../../shared/types/request-state';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../../../../core/entities/types/campaign/campaign-extras';
import {CampaignSettingsStoreFieldsErrorsState} from './campaign-settings.store.fields-errors-state';
import {CampaignGoalKPI} from '../../../../app.constants';

export class CampaignSettingsStoreState {
    entity: Campaign = {
        id: null,
        goals: [],
    };
    extras: CampaignExtras = {
        currency: null,
        campaignGoalsDefaults: {
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
    };
    fieldsErrors = new CampaignSettingsStoreFieldsErrorsState();
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
    };
}