import {APP_CONFIG} from '../../app.config';

const adGroupInternalApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;

export const BID_INSIGHTS_CONFIG = {
    requests: {
        bidInsights: {
            name: 'bidInsights',
            url: `${adGroupInternalApiUrl}/{adGroupId}/bidinsights/`,
        },
        dailyStats: {
            name: 'dailyStats',
            url: `${adGroupInternalApiUrl}/{adGroupId}/bidinsights/daily_stats/`,
        },
    },
};
