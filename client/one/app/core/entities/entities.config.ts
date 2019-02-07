import {APP_CONFIG} from '../../app.config';

const adGroupApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;

export const ENTITY_CONFIG = {
    requests: {
        adGroup: {
            get: {
                name: 'get',
                url: `${adGroupApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${adGroupApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${adGroupApiUrl}/`,
            },
            validate: {
                name: 'validate',
                url: `${adGroupApiUrl}/validate/`,
            },
            defaults: {
                name: 'defaults',
                url: `${adGroupApiUrl}/defaults/`,
            },
        },
    },
};
