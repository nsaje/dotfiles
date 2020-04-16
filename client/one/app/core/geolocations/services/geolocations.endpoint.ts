import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Geolocation} from '../types/geolocation';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {GeolocationType} from '../../../app.constants';
import {GEOLOCATIONS_CONFIG} from '../geolocations.config';

@Injectable()
export class GeolocationsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        nameContains: string | null,
        types: GeolocationType[] | null,
        keys: string[] | null,
        limit: number | null,
        offset: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Geolocation[]> {
        const request = GEOLOCATIONS_CONFIG.requests.geolocations.list;

        const params = {
            ...(commonHelpers.isDefined(types) && {
                types: types.join(','),
            }),
            ...(commonHelpers.isDefined(nameContains) && {nameContains}),
            ...(commonHelpers.isDefined(keys) && {
                keys: keys.join(','),
            }),
            ...(commonHelpers.isDefined(limit) && {
                limit: `${limit}`,
            }),
            ...(commonHelpers.isDefined(offset) && {
                offset: `${offset}`,
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Geolocation[]>>(request.url, {params})
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });
                    return throwError(error);
                })
            );
    }
}
