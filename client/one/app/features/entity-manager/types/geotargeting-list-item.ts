import {Geolocation} from '../../../core/geolocations/types/geolocation';
import {GeolocationType} from '../../../app.constants';

export interface GeotargetingListItem {
    name: string;
    type: GeolocationType;
    locations: Geolocation[];
}
