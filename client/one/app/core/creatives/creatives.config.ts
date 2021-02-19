import {APP_CONFIG} from '../../app.config';

const creativesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives`;
const creativeBatchesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives/batch`;
const creativeCandidatesApiUrl = `${APP_CONFIG.apiRestInternalUrl}/creatives/batch/{batchId}/candidates`;

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
                url: `${creativeBatchesApiUrl}/{batchId}`,
            },
            create: {
                name: 'createBatch',
                url: `${creativeBatchesApiUrl}/`,
            },
            edit: {
                name: 'editBatch',
                url: `${creativeBatchesApiUrl}/{batchId}`,
            },
            validate: {
                name: 'validateBatch',
                url: `${creativeBatchesApiUrl}/validate/`,
            },
        },
        creativeCandidates: {
            list: {
                name: 'listCandidates',
                url: `${creativeCandidatesApiUrl}/`,
            },
            create: {
                name: 'createCandidate',
                url: `${creativeCandidatesApiUrl}/`,
            },
            get: {
                name: 'getCandidate',
                url: `${creativeCandidatesApiUrl}/{candidateId}`,
            },
            edit: {
                name: 'editCandidate',
                url: `${creativeCandidatesApiUrl}/{candidateId}`,
            },
            remove: {
                name: 'removeCandidate',
                url: `${creativeCandidatesApiUrl}/{candidateId}`,
            },
        },
    },
};
