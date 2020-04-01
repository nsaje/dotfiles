import {APP_CONFIG} from '../../../app.config';
import {HttpRequestInfo} from '../../../shared/types/http-request-info';

const publisherGroupsInternalApiUrl = `${
    APP_CONFIG.apiRestInternalUrl
}/publishergroups`;
const publisherGroupsApiUrl = `${
    APP_CONFIG.apiLegacyUrl
}/accounts/{accountId}/publisher_groups`;

export const PUBLISHER_GROUPS_CONFIG: {
    requests: {publisherGroups: {[key: string]: HttpRequestInfo}};
} = {
    requests: {
        publisherGroups: {
            search: {
                name: 'search',
                url: `${publisherGroupsInternalApiUrl}/agencies/{agencyId}/search/`,
            },
            remove: {
                name: 'remove',
                url: `${publisherGroupsInternalApiUrl}/{publisherGroupId}/`,
            },
            list: {
                name: 'list',
                url: `${publisherGroupsApiUrl}/`,
            },
            upload: {
                name: 'upload',
                url: `${publisherGroupsApiUrl}/upload/`,
            },
            download: {
                name: 'download',
                url: `${publisherGroupsApiUrl}/{publisherGroupId}/download/`,
            },
            downloadErrors: {
                name: 'downloadErrors',
                url: `${publisherGroupsApiUrl}/errors/{csvKey}`,
            },
            downloadExample: {
                name: 'downloadExample',
                url: `${
                    APP_CONFIG.apiLegacyUrl
                }/publisher_groups/download/example/`,
            },
        },
    },
};
