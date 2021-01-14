import {GeolocationType} from '../../../app.constants';

export interface GeolocationSearchParams {
    nameContains: string;
    types: GeolocationType[];
    limit?: number;
    offset?: number;
    target: 'include' | 'exclude' | 'zip';
}
