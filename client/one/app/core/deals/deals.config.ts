import {APP_CONFIG} from '../../app.config';

const dealsApiUrl = `${APP_CONFIG.apiRestInternalUrl}/deals`;

export const DEALS_CONFIG = {
    requests: {
        deals: {
            get: {
                name: 'get',
                url: `${dealsApiUrl}/`,
            },
            list: {
                name: 'list',
                url: `${dealsApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${dealsApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${dealsApiUrl}/`,
            },
            remove: {
                name: 'remove',
                url: `${dealsApiUrl}/`,
            },
            validate: {
                name: 'validate',
                url: `${dealsApiUrl}/validate/`,
            },
        },
    },
};
