import {APP_CONFIG} from '../../app.config';

const historyApiUrl = `${APP_CONFIG.apiRestInternalUrl}/entityhistory/`;

export const ENTITY_HISTORY_CONFIG = {
    requests: {
        history: {
            name: 'history',
            url: historyApiUrl,
        },
    },
};
