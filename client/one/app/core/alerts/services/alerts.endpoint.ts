import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {Breakdown, Level} from '../../../app.constants';
import * as endpointHelpers from '../../../shared/helpers/endpoint.helpers';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as dateHelpers from '../../../shared/helpers/date.helpers';
import {ALERTS_CONFIG} from '../alerts.config';
import {HttpRequestInfo} from '../../../shared/types/http-request-info';
import {Alert} from '../types/alert';

@Injectable()
export class AlertsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        level: Level,
        entityId: string | null,
        breakdown: Breakdown | null,
        startDate: Date | null,
        endDate: Date | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Alert[]> {
        const request = this.getRequestInfo(level, entityId);
        const params = {
            ...(commonHelpers.isDefined(breakdown) && {
                breakdown: `${breakdown}`,
            }),
            ...(commonHelpers.isDefined(startDate) && {
                startDate: dateHelpers.convertDateToString(startDate),
            }),
            ...(commonHelpers.isDefined(endDate) && {
                endDate: dateHelpers.convertDateToString(endDate),
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Alert[]>>(request.url, {params: params})
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

    private getRequestInfo(
        level: Level,
        entityId: string | null
    ): HttpRequestInfo {
        switch (level) {
            case Level.ACCOUNTS:
                return endpointHelpers.replaceUrl(
                    ALERTS_CONFIG.requests.alerts.listAccount,
                    {
                        accountId: entityId,
                    }
                );
            case Level.CAMPAIGNS:
                return endpointHelpers.replaceUrl(
                    ALERTS_CONFIG.requests.alerts.listCampaign,
                    {
                        campaignId: entityId,
                    }
                );
            case Level.AD_GROUPS:
                return endpointHelpers.replaceUrl(
                    ALERTS_CONFIG.requests.alerts.listAdGroup,
                    {
                        adGroupId: entityId,
                    }
                );
            default:
                return ALERTS_CONFIG.requests.alerts.listAccounts;
        }
    }
}
