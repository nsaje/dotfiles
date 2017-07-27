interface AppConfig {
    staticUrl: String;
    env: {
        dev: boolean;
        test: boolean;
        prod: boolean;
    };
    buildNumber: String;
}
// APP_CONFIG is defined and injected by WebPack. This is just a wrapper to simplify APP_CONFIG imports in the app.
declare const APP_CONFIG: AppConfig;
const APP_CONFIG_EXPORT = APP_CONFIG;
export {APP_CONFIG_EXPORT as APP_CONFIG};
