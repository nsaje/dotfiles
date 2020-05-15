import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {APP_CONFIG} from '../../../app.config';
import {CREDITS_CONFIG} from '../credits.config';
import {Credit} from '../types/credit';
import {CreditRefund} from '../types/credit-refund';
import {CreditTotal} from '../types/credit-total';
import {CampaignBudget} from '../../entities/types/campaign/campaign-budget';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {replaceUrl} from '../../../shared/helpers/endpoint.helpers';

@Injectable()
export class CreditsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        active: boolean | null,
        limit: number,
        offset: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit[]> {
        const request = CREDITS_CONFIG.requests.credits.list;

        const params = {
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(active) && {
                active: active ? 'true' : 'false',
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
            .get<ApiResponse<Credit[]>>(request.url, {params})
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
        credit: Credit,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit> {
        const request = CREDITS_CONFIG.requests.credits.create;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<Credit>>(request.url, credit).pipe(
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
        credit: Credit,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit> {
        const request = replaceUrl(CREDITS_CONFIG.requests.credits.edit, {
            creditId: credit.id,
        });

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.put<ApiResponse<Credit>>(request.url, credit).pipe(
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

    totals(
        agencyId: string | null,
        accountId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditTotal> {
        const request = CREDITS_CONFIG.requests.credits.totals;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = {
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
        };

        return this.http
            .get<ApiResponse<CreditTotal>>(request.url, {params})
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

    listBudgets(
        creditId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CampaignBudget[]> {
        const request = replaceUrl(
            CREDITS_CONFIG.requests.credits.listBudgets,
            {creditId: creditId}
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<CampaignBudget[]>>(request.url).pipe(
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

    listRefunds(
        agencyId: string | null,
        accountId: string | null,
        limit: number,
        offset: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditRefund[]> {
        const request = CREDITS_CONFIG.requests.credits.listRefunds;

        const params = {
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
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
            .get<ApiResponse<CreditRefund[]>>(request.url, {params})
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

    createRefund(
        creditId: string,
        creditRefund: CreditRefund,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditRefund> {
        const request = replaceUrl(
            CREDITS_CONFIG.requests.credits.createRefund,
            {creditId: creditId}
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<CreditRefund>>(request.url, creditRefund)
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
