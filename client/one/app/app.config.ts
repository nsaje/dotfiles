import {environment} from '../environments/environment';

export const APP_CONFIG = {
    env: environment.env,
    buildNumber: environment.buildNumber,
    branchName: environment.branchName,
    sentryToken: environment.sentryToken,
    staticUrl: environment.staticUrl,
    apiLegacyUrl: '/api',
    apiRestUrl: '/rest',
    apiRestInternalUrl: '/rest/internal',
    maxQueryParamsLength: 1900,
    GAKey: 'UA-74379813-2',
};
