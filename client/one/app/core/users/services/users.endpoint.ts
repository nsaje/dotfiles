import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {User} from '../types/user';
import {USERS_CONFIG} from './users.config';
import {replaceUrl} from '../../../shared/helpers/endpoint.helpers';
import {isDefined} from '../../../shared/helpers/common.helpers';

@Injectable()
export class UsersEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        showInternal: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User[]> {
        const request = USERS_CONFIG.requests.users.list;

        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(isDefined(agencyId) && {agencyId}),
            ...(isDefined(accountId) && {accountId}),
            ...(isDefined(keyword) && {keyword}),
            ...(isDefined(showInternal) && {
                showInternal: `${showInternal}`,
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<User[]>>(request.url, {params})
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
        users: User[],
        agencyId: string,
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User[]> {
        const request = USERS_CONFIG.requests.users.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = this.getScopeParams(agencyId, accountId);

        return this.http
            .post<ApiResponse<User[]>>(request.url, {users}, {params})
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
        user: Partial<User>,
        agencyId: string,
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = USERS_CONFIG.requests.users.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = this.getScopeParams(agencyId, accountId);

        return this.http
            .post<ApiResponse<void>>(request.url, user, {params})
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

    get(
        userId: string,
        agencyId: string,
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User> {
        const request = replaceUrl(USERS_CONFIG.requests.users.get, {
            userId: userId,
        });

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = this.getScopeParams(agencyId, accountId);

        return this.http
            .get<ApiResponse<User>>(request.url, {params})
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

    edit(
        user: Partial<User>,
        agencyId: string,
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User> {
        const request = replaceUrl(USERS_CONFIG.requests.users.edit, {
            userId: user.id,
        });

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = this.getScopeParams(agencyId, accountId);

        return this.http
            .put<ApiResponse<User>>(request.url, user, {params})
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
        userId: string,
        agencyId: string,
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = replaceUrl(USERS_CONFIG.requests.users.remove, {
            userId: userId,
        });

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const params = this.getScopeParams(agencyId, accountId);

        return this.http
            .delete<ApiResponse<User>>(request.url, {params})
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

    private getScopeParams(agencyId: string, accountId: string): any {
        return {
            ...(isDefined(agencyId) &&
                !isDefined(accountId) && {agencyId: agencyId}),
            ...(isDefined(accountId) && {accountId}),
        };
    }
}
