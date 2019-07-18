import {CampaignExtras} from '../../core/entities/types/campaign/campaign-extras';
import {CampaignGoalKPI} from '../../app.constants';

export const campaignExtrasMock: CampaignExtras = {
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
};
