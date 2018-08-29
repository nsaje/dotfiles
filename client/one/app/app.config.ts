import {environment} from '../environments/environment';

interface AppConfig {
    env: {
        dev: boolean;
        test: boolean;
        prod: boolean;
    };
    buildNumber: String;
    branchName: String;
    sentryToken: String;
    staticUrl: String;
}

export const APP_CONFIG: AppConfig = {
    env: environment.env,
    buildNumber: environment.buildNumber,
    branchName: environment.branchName,
    sentryToken: environment.sentryToken,
    staticUrl: environment.staticUrl,
};

// TODO: add options when needed in Angular app
