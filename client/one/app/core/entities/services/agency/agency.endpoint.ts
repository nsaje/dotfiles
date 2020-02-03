import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ENTITY_CONFIG} from '../../entities.config';
import {ApiResponse} from '../../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Agency} from '../../types/agency/agency';

@Injectable()
export class AgencyEndpoint {
    constructor(private http: HttpClient) {}

    list(requestStateUpdater: RequestStateUpdater): Observable<Agency[]> {
        const request = ENTITY_CONFIG.requests.agency.list;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Agency[]>>(request.url).pipe(
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
