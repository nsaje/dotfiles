import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {BidInsights} from '../types/bid-insights';
import {BidInsightsDailyStats} from '../types/bid-insights-daily-stats';
import {BidInsightsEndpoint} from './bid-insights.endpoint';

@Injectable()
export class BidInsightsService {
    constructor(private endpoint: BidInsightsEndpoint) {}

    getBidInsights(
        adGroupId: string,
        datetimeFrom: Date,
        datetimeTo: Date,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidInsights> {
        return this.endpoint.getBidInsights(
            adGroupId,
            datetimeFrom,
            datetimeTo,
            requestStateUpdater
        );
    }

    getDailyStats(
        adGroupId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidInsightsDailyStats[]> {
        return this.endpoint.getDailyStats(adGroupId, requestStateUpdater);
    }
}
