import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {PublisherGroup} from '../types/publisher-group';
import {APP_CONFIG} from '../../../app.config';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class PublisherGroupsEndpoint {
    constructor(private http: HttpClient) {}

    search(
        agencyId: string,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/publishergroups/search/`,
            name: 'search',
        };

        if (!commonHelpers.isDefined(keyword)) {
            keyword = '';
        }

        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            keyword: `${keyword}`,
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<PublisherGroup[]>>(request.url, {
                params: params,
            })
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        count: response.count,
                        next: response.next,
                        previous: response.previous,
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
