import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {Rule} from '../types/rule';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {APP_CONFIG} from '../../../app.config';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';

@Injectable()
export class RulesEndpoint {
    constructor(private http: HttpClient) {}

    create(
        agencyId: string,
        rule: Rule,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        const request = {
            url: `${APP_CONFIG.apiRestInternalUrl}/agencies/${agencyId}/rules/`,
            name: 'create',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<Rule>>(request.url, rule).pipe(
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
