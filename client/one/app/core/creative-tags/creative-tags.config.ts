import {APP_CONFIG} from '../../app.config';

const creativeTagsApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creativetags`;

export const CREATIVE_TAGS_CONFIG = {
    requests: {
        creatives: {
            list: {
                name: 'list',
                url: `${creativeTagsApiUrl}/`,
            },
        },
    },
};
