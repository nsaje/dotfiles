import {CampaignGoalKPI} from '../../../../app.constants';

export const AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG = {
    optimizationObjectivesTexts: {
        [CampaignGoalKPI.TIME_ON_SITE]: 'time on site',
        [CampaignGoalKPI.MAX_BOUNCE_RATE]: 'bounce rate',
        [CampaignGoalKPI.PAGES_PER_SESSION]: 'pages per session',
        [CampaignGoalKPI.CPV]: 'cost per visit',
        [CampaignGoalKPI.CPC]: 'average CPC',
        [CampaignGoalKPI.NEW_UNIQUE_VISITORS]: 'new users',
        [CampaignGoalKPI.CPA]: 'CPA',
        [CampaignGoalKPI.CP_NON_BOUNCED_VISIT]: 'cost per non-bounced visit',
        [CampaignGoalKPI.CP_NEW_VISITOR]: 'cost per new visitor',
        [CampaignGoalKPI.CP_PAGE_VIEW]: 'cost per pageview',
        [CampaignGoalKPI.CPCV]: 'cost per completed video view',
        default: 'maximum value',
    },
};
