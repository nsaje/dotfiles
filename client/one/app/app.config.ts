import {environment} from '../environments/environment';

export const APP_CONFIG = {
    env: environment.env,
    buildNumber: environment.buildNumber,
    branchName: environment.branchName,
    sentryToken: environment.sentryToken,
    staticUrl: environment.staticUrl,
    api_legacy_url: '/api',
    api_rest_url: '/rest',
    api_rest_internal_url: '/rest/internal',
    max_query_params_length: 1900,
};
