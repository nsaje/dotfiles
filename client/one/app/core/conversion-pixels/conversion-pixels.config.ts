import {APP_CONFIG} from '../../app.config';

const conversionPixelsApiUrl = `${APP_CONFIG.apiRestUrl}/v1/accounts`;

export const CONVERSION_PIXELS_CONFIG = {
    requests: {
        conversionPixels: {
            list: {
                name: 'list',
                url: `${conversionPixelsApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${conversionPixelsApiUrl}/`,
            },
            edit: {
                name: 'edit',
                url: `${conversionPixelsApiUrl}/`,
            },
        },
    },
};
