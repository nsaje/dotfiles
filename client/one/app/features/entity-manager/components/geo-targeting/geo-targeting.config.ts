import {GeolocationType} from '../../../../app.constants';

export const GEOLOCATION_TYPE_VALUE_TEXT = {
    [GeolocationType.COUNTRY]: 'Country',
    [GeolocationType.REGION]: 'State / Region',
    [GeolocationType.DMA]: 'DMA®',
    [GeolocationType.CITY]: 'City',
    [GeolocationType.ZIP]: 'Postal Code',
};

export const ITEM_LIST_LIMIT = 5;
