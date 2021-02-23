import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {BidInsights} from '../types/bid-insights';
import {BID_INSIGHTS_CONFIG} from '../bid-insights.config';
import {replaceUrl} from '../../../shared/helpers/endpoint.helpers';
import {ApiResponse} from '../../../shared/types/api-response';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as dateHelpers from '../../../shared/helpers/date.helpers';
import {map, catchError} from 'rxjs/operators';
import {BidInsightsDailyStats} from '../types/bid-insights-daily-stats';

@Injectable()
export class BidInsightsEndpoint {
    constructor(private http: HttpClient) {}

    getBidInsights(
        adGroupId: string,
        datetimeFrom: Date,
        datetimeTo: Date,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidInsights> {
        const request = replaceUrl(BID_INSIGHTS_CONFIG.requests.bidInsights, {
            adGroupId,
        });

        const params = {
            ...(commonHelpers.isDefined(datetimeFrom) && {
                datetimeFromUtc: dateHelpers.convertDateTimeToUTCString(
                    datetimeFrom
                ),
            }),
            ...(commonHelpers.isDefined(datetimeTo) && {
                datetimeToUtc: dateHelpers.convertDateTimeToUTCString(
                    datetimeTo
                ),
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<BidInsights>>(request.url, {params: params})
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

    getDailyStats(
        adGroupId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidInsightsDailyStats[]> {
        const request = replaceUrl(BID_INSIGHTS_CONFIG.requests.dailyStats, {
            adGroupId,
        });

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<BidInsightsDailyStats[]>>(request.url)
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
