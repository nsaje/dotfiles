import {APP_CONFIG} from '../../../app.config';
import {HttpRequestInfo} from '../../../shared/types/http-request-info';

const publisherGroupsInternalApiUrl = `${APP_CONFIG.apiRestInternalUrl}/publishergroups`;
const publisherGroupsLegacyApiUrl = `${APP_CONFIG.apiLegacyUrl}/publisher_groups`;

export const PUBLISHER_GROUPS_CONFIG: {
    requests: {publisherGroups: {[key: string]: HttpRequestInfo}};
} = {
    requests: {
        publisherGroups: {
            search: {
                name: 'search',
                url: `${publisherGroupsInternalApiUrl}/`,
            },
            remove: {
                name: 'remove',
                url: `${publisherGroupsInternalApiUrl}/{publisherGroupId}/`,
            },
            list: {
                name: 'list',
                url: `${publisherGroupsLegacyApiUrl}/`,
            },
            upload: {
                name: 'upload',
                url: `${publisherGroupsLegacyApiUrl}/upload/`,
            },
            download: {
                name: 'download',
                url: `${publisherGroupsLegacyApiUrl}/{publisherGroupId}/download/`,
            },
            downloadErrors: {
                name: 'downloadErrors',
                url: `${publisherGroupsLegacyApiUrl}/errors/{csvKey}`,
            },
            downloadExample: {
                name: 'downloadExample',
                url: `${publisherGroupsLegacyApiUrl}/download/example/`,
            },
            addEntries: {
                name: 'addEntries',
                url: `${publisherGroupsInternalApiUrl}/add/`,
            },
        },
    },
};
