import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {Creative} from '../types/creative';
import {CREATIVES_CONFIG} from '../creatives.config';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {ApiResponse} from '../../../shared/types/api-response';
import {catchError, map} from 'rxjs/operators';
import {AdType} from '../../../app.constants';
import {CreativeBatch} from '../types/creative-batch';

@Injectable()
export class CreativesEndpoint {
    constructor(private http: HttpClient) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        creativeType: AdType | null,
        tags: string[] | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Creative[]> {
        const request = CREATIVES_CONFIG.requests.creatives.list;
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
            ...(commonHelpers.isDefined(creativeType) && {
                creativeType: AdType[creativeType],
            }),
            ...(commonHelpers.isDefined(tags) && {tags: tags.join(',')}),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Creative[]>>(request.url, {params})
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

    getBatch(
        batchId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        const request = CREATIVES_CONFIG.requests.creativeBatches.get;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<CreativeBatch>>(`${request.url}${batchId}`)
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

    createBatch(
        batch: CreativeBatch,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        const request = CREATIVES_CONFIG.requests.creativeBatches.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<CreativeBatch>>(request.url, batch)
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

    editBatch(
        batch: CreativeBatch,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        const request = CREATIVES_CONFIG.requests.creativeBatches.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<CreativeBatch>>(`${request.url}${batch.id}`, batch)
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

    validateBatch(
        batch: Partial<CreativeBatch>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = CREATIVES_CONFIG.requests.creativeBatches.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<void>>(request.url, batch).pipe(
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
