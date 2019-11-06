import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Deal} from '../types/deal';
import {DealConnection} from '../types/deal-connection';
import {APP_CONFIG} from '../../../app.config';

@Injectable()
export class DealsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal[]> {
        const request = {
            url: `${APP_CONFIG.apiRestInternalUrl}/agencies/${agencyId}/deals/`,
            name: 'list',
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Deal[]>>(request.url, {
                params: {
                    offset: `${offset}`,
                    limit: `${limit}`,
                    keyword: keyword,
                },
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

    create(
        agencyId: string,
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = {
            url: `${APP_CONFIG.apiRestInternalUrl}/agencies/${agencyId}/deals/`,
            name: 'create',
        };
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
        agencyId: string,
        deal: Partial<Deal>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/deals/validate/`,
            name: 'validate',
        };
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
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/deals/${dealId}`,
            name: 'get',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Deal>>(request.url).pipe(
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
        agencyId: string,
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        const request = {
            url: `${APP_CONFIG.apiRestInternalUrl}/agencies/${agencyId}/deals/${
                deal.id
            }`,
            name: 'edit',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.put<ApiResponse<Deal>>(request.url, deal).pipe(
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
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/deals/${dealId}`,
            name: 'remove',
        };
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.delete<ApiResponse<Deal>>(request.url).pipe(
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
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<DealConnection[]> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/deals/${dealId}/connections/`,
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
        agencyId: string,
        dealId: string,
        dealConnectionId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = {
            url: `${
                APP_CONFIG.apiRestInternalUrl
            }/agencies/${agencyId}/deals/${dealId}/connections/${dealConnectionId}`,
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
