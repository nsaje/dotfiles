import {APP_CONFIG} from '../../../app.config';

const publisherGroupsSearchApiUrl = `${
    APP_CONFIG.apiRestInternalUrl
}/agencies/{agencyId}/publishergroups`;
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
                url: `${publisherGroupsSearchApiUrl}/search/`,
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
