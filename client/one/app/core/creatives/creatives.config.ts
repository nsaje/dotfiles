import {APP_CONFIG} from '../../app.config';

const creativesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives`;
const creativeBatchesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives/batch`;

export const CREATIVES_CONFIG = {
    requests: {
        creatives: {
            list: {
                name: 'list',
                url: `${creativesApiUrl}/`,
            },
        },
        creativeBatches: {
            get: {
                name: 'getBatch',
                url: `${creativeBatchesApiUrl}/`,
            },
            create: {
                name: 'createBatch',
                url: `${creativeBatchesApiUrl}/`,
            },
            edit: {
                name: 'editBatch',
                url: `${creativeBatchesApiUrl}/`,
            },
            validate: {
                name: 'validateBatch',
                url: `${creativeBatchesApiUrl}/validate/`,
            },
        },
    },
};
