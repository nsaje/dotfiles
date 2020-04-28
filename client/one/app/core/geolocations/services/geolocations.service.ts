import {Injectable} from '@angular/core';
import {GeolocationsEndpoint} from './geolocations.endpoint';
import {Geolocation} from '../types/geolocation';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {GeolocationType} from '../../../app.constants';

@Injectable()
export class GeolocationsService {
    constructor(private endpoint: GeolocationsEndpoint) {}

    list(
        nameContains: string | null,
        type: GeolocationType | null,
        keys: string[] | null,
        limit: number | null,
        offset: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Geolocation[]> {
        return this.endpoint.list(
            nameContains,
            type,
            keys,
            limit,
            offset,
            requestStateUpdater
        );
    }
}
