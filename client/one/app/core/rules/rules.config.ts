import {APP_CONFIG} from '../../app.config';

const rulesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/rules`;

export const RULES_CONFIG = {
    requests: {
        rules: {
            get: {
                name: 'get',
                url: `${rulesApiUrl}/{ruleId}/`,
            },
            list: {
                name: 'list',
                url: `${rulesApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${rulesApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${rulesApiUrl}/{ruleId}/`,
            },
            listHistories: {
                name: 'listHistories',
                url: `${rulesApiUrl}/history/`,
            },
        },
    },
};
