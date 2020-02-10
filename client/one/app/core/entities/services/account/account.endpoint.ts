import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {AccountWithExtras} from '../../types/account/account-with-extras';
import {ENTITY_CONFIG} from '../../entities.config';
import {ApiResponse} from '../../../../shared/types/api-response';
import {Account} from '../../types/account/account';
import {AccountExtras} from '../../types/account/account-extras';
import {map, catchError} from 'rxjs/operators';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Injectable()
export class AccountEndpoint {
    constructor(private http: HttpClient) {}

    defaults(
        requestStateUpdater: RequestStateUpdater
    ): Observable<AccountWithExtras> {
        const request = ENTITY_CONFIG.requests.account.defaults;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Account, AccountExtras>>(request.url)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        account: response.data,
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
    ): Observable<AccountWithExtras> {
        const request = ENTITY_CONFIG.requests.account.get;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Account, AccountExtras>>(`${request.url}${id}`)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        account: response.data,
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

    list(
        agencyId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account[]> {
        const request = ENTITY_CONFIG.requests.account.list;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = {
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
        };

        return this.http
            .get<ApiResponse<Account[]>>(request.url, {params})
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

    validate(
        account: Partial<Account>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = ENTITY_CONFIG.requests.account.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<void>>(request.url, account).pipe(
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
        account: Account,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        const request = ENTITY_CONFIG.requests.account.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<Account>>(request.url, account).pipe(
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
        account: Partial<Account>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        const request = ENTITY_CONFIG.requests.account.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<Account>>(`${request.url}${account.id}`, account)
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
