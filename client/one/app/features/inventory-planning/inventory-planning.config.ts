import {APP_CONFIG} from '../../app.config';

const apiUrl = `${APP_CONFIG.apiRestInternalUrl}/inventory-planning`;

export const INVENTORY_PLANNING_CONFIG = {
    requests: {
        loadSummary: {
            name: 'summary',
            url: `${apiUrl}/summary`,
        },
        loadCountries: {
            name: 'countries',
            url: `${apiUrl}/countries`,
        },
        loadPublishers: {
            name: 'publishers',
            url: `${apiUrl}/publishers`,
        },
        loadDevices: {
            name: 'devices',
            url: `${apiUrl}/device-types`,
        },
        loadSources: {
            name: 'sources',
            url: `${apiUrl}/media-sources`,
        },
        loadChannels: {
            name: 'channels',
            url: `${apiUrl}/channels`,
        },
    },
};
