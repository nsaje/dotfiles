import {APP_CONFIG} from '../../app.config';

const adGroupApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;
const campaignApiUrl = `${APP_CONFIG.apiRestInternalUrl}/campaigns`;

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
        campaign: {
            get: {
                name: 'get',
                url: `${campaignApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${campaignApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${campaignApiUrl}/`,
            },
            validate: {
                name: 'validate',
                url: `${campaignApiUrl}/validate/`,
            },
            defaults: {
                name: 'defaults',
                url: `${campaignApiUrl}/defaults/`,
            },
        },
    },
};
