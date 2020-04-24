import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Source} from '../types/source';
import {APP_CONFIG} from '../../../app.config';

@Injectable()
export class SourcesEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Source[]> {
        const request = {
            url: `${APP_CONFIG.apiRestInternalUrl}/agencies/${agencyId}/sources/`,
            name: 'list',
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Source[]>>(request.url).pipe(
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
