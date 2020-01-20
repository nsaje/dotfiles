import {Injectable} from '@angular/core';
import {HttpClient, HttpParams, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {CampaignWithExtras} from '../../types/campaign/campaign-with-extras';
import {ENTITY_CONFIG} from '../../entities.config';
import {ApiResponse} from '../../../../shared/types/api-response';
import {Campaign} from '../../types/campaign/campaign';
import {CampaignExtras} from '../../types/campaign/campaign-extras';
import {map, catchError} from 'rxjs/operators';
import {CampaignCloneSettings} from '../../types/campaign/campaign-clone-settings';

@Injectable()
export class CampaignEndpoint {
    constructor(private http: HttpClient) {}

    defaults(
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CampaignWithExtras> {
        const request = ENTITY_CONFIG.requests.campaign.defaults;
        const params = new HttpParams().set('accountId', accountId);

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Campaign, CampaignExtras>>(request.url, {
                params: params,
            })
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        campaign: response.data,
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
    ): Observable<CampaignWithExtras> {
        const request = ENTITY_CONFIG.requests.campaign.get;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Campaign, CampaignExtras>>(`${request.url}${id}`)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return {
                        campaign: response.data,
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
        campaign: Partial<Campaign>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = ENTITY_CONFIG.requests.campaign.validate;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<void>>(request.url, campaign).pipe(
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
        campaign: Campaign,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        const request = ENTITY_CONFIG.requests.campaign.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<Campaign>>(request.url, campaign)
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
        campaign: Partial<Campaign>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        const request = ENTITY_CONFIG.requests.campaign.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<Campaign>>(
                `${request.url}${campaign.id}`,
                campaign
            )
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

    clone(
        campaignId: string,
        requestData: CampaignCloneSettings,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        const request = ENTITY_CONFIG.requests.campaign.clone;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<Campaign>>(
                `${request.url}${campaignId}`,
                requestData
            )
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
