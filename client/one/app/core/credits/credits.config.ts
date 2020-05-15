import {APP_CONFIG} from '../../app.config';

const creditsApiUrl = `${APP_CONFIG.apiRestInternalUrl}/credits`;

export const CREDITS_CONFIG = {
    requests: {
        credits: {
            list: {
                name: 'list',
                url: `${creditsApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${creditsApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${creditsApiUrl}/{creditId}`,
            },
            totals: {
                name: 'totals',
                url: `${creditsApiUrl}/totals/`,
            },
            listBudgets: {
                name: 'listBudgets',
                url: `${creditsApiUrl}/{creditId}/budgets/`,
            },
            listRefunds: {
                name: 'listRefunds',
                url: `${creditsApiUrl}/refunds/`,
            },
            createRefund: {
                name: 'createRefund',
                url: `${creditsApiUrl}/{creditId}/refunds/`,
            },
        },
    },
};
