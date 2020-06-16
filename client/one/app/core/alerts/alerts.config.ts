import {APP_CONFIG} from '../../app.config';

export const ALERTS_CONFIG = {
    requests: {
        alerts: {
            listAccounts: {
                name: 'listAccounts',
                url: `${APP_CONFIG.apiRestInternalUrl}/accounts/alerts`,
            },
            listAccount: {
                name: 'listAccount',
                url: `${APP_CONFIG.apiRestInternalUrl}/accounts/{accountId}/alerts`,
            },
            listCampaign: {
                name: 'listCampaign',
                url: `${APP_CONFIG.apiRestInternalUrl}/campaigns/{campaignId}/alerts`,
            },
            listAdGroup: {
                name: 'listAdGroup',
                url: `${APP_CONFIG.apiRestInternalUrl}/adgroups/{adGroupId}/alerts`,
            },
        },
    },
};
