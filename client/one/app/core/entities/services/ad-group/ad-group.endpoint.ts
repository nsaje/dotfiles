import {Injectable} from '@angular/core';
import {HttpClient, HttpParams, HttpErrorResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {map, catchError} from 'rxjs/operators';
import {ApiResponse} from '../../../../shared/types/api-response';
import {ENTITY_CONFIG} from '../../entities.config';
import {AdGroupWithExtras} from '../../types/ad-group/ad-group-with-extras';
import {AdGroup} from '../../types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {AdGroupExtras} from '../../types/ad-group/ad-group-extras';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Injectable()
export class AdGroupEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number,
        limit: number,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup[]> {
        const request = ENTITY_CONFIG.requests.adGroup.list;

        const params = {
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(limit) && {
                limit: `${limit}`,
            }),
            ...(commonHelpers.isDefined(offset) && {
                offset: `${offset}`,
            }),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<AdGroup[]>>(request.url, {params})
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

    defaults(
        campaignId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroupWithExtras> {
        const request = ENTITY_CONFIG.requests.adGroup.defaults;
        const params = new HttpParams().set('campaignId', campaignId);

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<AdGroup, AdGroupExtras>>(request.url, {
                params: params,
            })
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        adGroup: response.data,
                        extras: response.extra,
                    };
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

    get(
        id: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroupWithExtras> {
        const request = ENTITY_CONFIG.requests.adGroup.get;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<AdGroup, AdGroupExtras>>(`${request.url}${id}`)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        adGroup: response.data,
                        extras: response.extra,
                    };
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

    validate(
        adGroup: Partial<AdGroup>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = ENTITY_CONFIG.requests.adGroup.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<void>>(request.url, adGroup).pipe(
            map(response => {
                requestStateUpdater(request.name, {
                    inProgress: false,
                });
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

    create(
        adGroup: AdGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        const request = ENTITY_CONFIG.requests.adGroup.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<AdGroup>>(request.url, adGroup).pipe(
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

    edit(
        adGroup: Partial<AdGroup>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        const request = ENTITY_CONFIG.requests.adGroup.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<AdGroup>>(`${request.url}${adGroup.id}`, adGroup)
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
