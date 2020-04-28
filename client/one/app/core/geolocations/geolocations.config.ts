import {APP_CONFIG} from '../../app.config';
import {GeolocationType} from '../../app.constants';

const geolocationsApiUrl = `${APP_CONFIG.apiRestUrl}/v1/geolocations`;

export const GEOLOCATIONS_CONFIG = {
    requests: {
        geolocations: {
            list: {
                name: 'list',
                url: `${geolocationsApiUrl}/`,
            },
            [`list${GeolocationType.COUNTRY}`]: {
                name: 'listCountry',
                url: `${geolocationsApiUrl}/`,
            },
            [`list${GeolocationType.REGION}`]: {
                name: 'listRegion',
                url: `${geolocationsApiUrl}/`,
            },
            [`list${GeolocationType.DMA}`]: {
                name: 'listDma',
                url: `${geolocationsApiUrl}/`,
            },
            [`list${GeolocationType.CITY}`]: {
                name: 'listCity',
                url: `${geolocationsApiUrl}/`,
            },
            [`list${GeolocationType.ZIP}`]: {
                name: 'listZip',
                url: `${geolocationsApiUrl}/`,
            },
        },
    },
};
