import {APP_CONFIG} from '../../app.config';

const geolocationsApiUrl = `${APP_CONFIG.apiRestUrl}/v1/geolocations`;

export const GEOLOCATIONS_CONFIG = {
    requests: {
        geolocations: {
            list: {
                name: 'list',
                url: `${geolocationsApiUrl}/`,
            },
        },
    },
};
