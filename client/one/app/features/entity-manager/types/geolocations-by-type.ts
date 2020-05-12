import {GeolocationType} from '../../../app.constants';
import {Geolocation} from '../../../core/geolocations/types/geolocation';

export interface GeolocationsByType {
    [GeolocationType.COUNTRY]: Geolocation[];
    [GeolocationType.REGION]: Geolocation[];
    [GeolocationType.DMA]: Geolocation[];
    [GeolocationType.CITY]: Geolocation[];
    [GeolocationType.ZIP]: Geolocation[];
}
