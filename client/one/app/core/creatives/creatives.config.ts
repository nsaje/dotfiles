import {APP_CONFIG} from '../../app.config';

const creativesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives`;

export const CREATIVES_CONFIG = {
    requests: {
        creatives: {
            list: {
                name: 'list',
                url: `${creativesApiUrl}/`,
            },
        },
    },
};
