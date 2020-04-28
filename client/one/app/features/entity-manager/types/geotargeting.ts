import {Geolocation} from '../../../core/geolocations/types/geolocation';
import {IncludeExcludeType} from '../../../app.constants';

export interface Geotargeting {
    selectedLocation: Geolocation;
    includeExcludeType: IncludeExcludeType;
    zipCodes?: string[];
}
