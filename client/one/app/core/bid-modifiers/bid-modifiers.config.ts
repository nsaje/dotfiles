import {APP_CONFIG} from '../../app.config';

const adGroupApiUrl = `${APP_CONFIG.apiRestUrl}/v1/adgroups`;

export const BID_MODIFIER_CONFIG = {
    requests: {
        save: {
            name: 'save',
            url: `${adGroupApiUrl}/`,
        },
    },
};
