import {APP_CONFIG} from '../../app.config';

const adGroupApiUrl = `${APP_CONFIG.apiRestUrl}/v1/adgroups`;
const adGroupInternalApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;

export const BID_MODIFIER_CONFIG = {
    requests: {
        save: {
            name: 'save',
            url: `${adGroupApiUrl}/`,
        },
        import: {
            name: 'import',
            url: `${adGroupInternalApiUrl}/`,
        },
    },
};
