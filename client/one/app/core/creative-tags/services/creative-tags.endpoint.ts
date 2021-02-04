import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {CREATIVE_TAGS_CONFIG} from '../creative-tags.config';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {ApiResponse} from '../../../shared/types/api-response';
import {catchError, map} from 'rxjs/operators';

@Injectable()
export class CreativeTagsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<string[]> {
        const request = CREATIVE_TAGS_CONFIG.requests.creativeTags.list;
        const params = {
            ...(commonHelpers.isDefined(offset) && {offset: `${offset}`}),
            ...(commonHelpers.isDefined(limit) && {limit: `${limit}`}),
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<string[]>>(request.url, {params})
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
