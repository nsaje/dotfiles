import {GeolocationType} from '../../../app.constants';

export interface Geolocation {
    key: string | null;
    type: GeolocationType | null;
    name: string;
    outbrainId: string | null;
    woeid: string | null;
    facebookKey: string | null;
}
