import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Deal} from '../types/deal';
import {DealConnection} from '../types/deal-connection';
import {APP_CONFIG} from '../../../app.config';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {DEALS_CONFIG} from './deals.config';

@Injectable()
export class DealsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        agencyOnly: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal[]> {
        const request = DEALS_CONFIG.requests.deals.list;
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
            ...(commonHelpers.isDefined(agencyOnly) && {
                agencyOnly: `${agencyOnly}`,
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Deal[]>>(request.url, {params}).pipe(
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

    create(
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = DEALS_CONFIG.requests.deals.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<Deal>>(request.url, deal).pipe(
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

    validate(
        deal: Partial<Deal>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = DEALS_CONFIG.requests.deals.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<void>>(request.url, deal).pipe(
            map(() => {
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

    get(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = DEALS_CONFIG.requests.deals.get;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Deal>>(`${request.url}${dealId}`).pipe(
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
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = DEALS_CONFIG.requests.deals.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<Deal>>(`${request.url}${deal.id}`, deal)
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

    remove(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = DEALS_CONFIG.requests.deals.remove;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .delete<ApiResponse<Deal>>(`${request.url}${dealId}`)
            .pipe(
                map(() => {
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

    listConnections(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<DealConnection[]> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/deals/${dealId}/connections/`,
            name: 'listConnections',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<DealConnection[]>>(request.url).pipe(
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

    removeConnection(
        dealId: string,
        dealConnectionId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/deals/${dealId}/connections/${dealConnectionId}`,
            name: 'removeConnection',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.delete<ApiResponse<DealConnection>>(request.url).pipe(
            map(() => {
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
}
