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
import {replaceUrl} from '../../../shared/helpers/endpoint.helpers';
import {CreativeCandidate} from '../types/creative-candidate';

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
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeBatches.get,
            {
                batchId,
            }
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<CreativeBatch>>(request.url).pipe(
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
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeBatches.edit,
            {
                batchId: batch.id,
            }
        );
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<CreativeBatch>>(request.url, batch)
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

    listCandidates(
        batchId: string,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate[]> {
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeCandidates.list,
            {
                batchId,
            }
        );
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<CreativeCandidate[]>>(request.url, {params})
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

    createCandidate(
        batchId: string,
        candidate: CreativeCandidate,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeCandidates.create,
            {
                batchId,
            }
        );
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<CreativeCandidate>>(request.url, candidate)
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

    getCandidate(
        batchId: string,
        candidateId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeCandidates.get,
            {
                batchId,
                candidateId,
            }
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<CreativeCandidate>>(request.url).pipe(
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

    editCandidate(
        batchId: string,
        candidateId: string,
        changes: Partial<CreativeCandidate>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeCandidates.edit,
            {
                batchId,
                candidateId,
            }
        );
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<CreativeCandidate>>(request.url, changes)
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

    removeCandidate(
        batchId: string,
        candidateId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = replaceUrl(
            CREATIVES_CONFIG.requests.creativeCandidates.remove,
            {
                batchId,
                candidateId,
            }
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.delete<ApiResponse<void>>(request.url).pipe(
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
}
