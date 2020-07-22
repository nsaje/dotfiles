import {APP_CONFIG} from '../../app.config';

const adGroupApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;
const campaignApiUrl = `${APP_CONFIG.apiRestInternalUrl}/campaigns`;
const accountApiUrl = `${APP_CONFIG.apiRestInternalUrl}/accounts`;
const agencyApiUrl = `${APP_CONFIG.apiRestInternalUrl}/agencies`;

export const ENTITY_CONFIG = {
    requests: {
        adGroup: {
            list: {
                name: 'list',
                url: `${adGroupApiUrl}/`,
            },
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
            list: {
                name: 'list',
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
            clone: {
                name: 'clone',
                url: `${campaignApiUrl}/`,
            },
        },
        account: {
            get: {
                name: 'get',
                url: `${accountApiUrl}/`,
            },
            list: {
                name: 'list',
                url: `${accountApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${accountApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${accountApiUrl}/`,
            },
            validate: {
                name: 'validate',
                url: `${accountApiUrl}/validate/`,
            },
            defaults: {
                name: 'defaults',
                url: `${accountApiUrl}/defaults/`,
            },
        },
        agency: {
            list: {
                name: 'list',
                url: `${agencyApiUrl}/`,
            },
        },
    },
};
