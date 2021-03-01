import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {BidInsightsEndpoint} from './bid-insights.endpoint';
import {BidInsightsService} from './bid-insights.service';
import {BidInsights} from '../types/bid-insights';
import {BidInsightsDailyStats} from '../types/bid-insights-daily-stats';

describe('BidInsightsService', () => {
    let service: BidInsightsService;
    let endpointStub: jasmine.SpyObj<BidInsightsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;
    const adGroupId = '1234';
    const date = new Date();

    const mockedBidInsights: BidInsights = {
        bidRequests: 1000,
        targetingEligibleRate: 0.8,
        budgetEligibleRate: 0.7,
        creativesEligibleRate: 0.6,
        internalAutctionEligibleRate: 0.5,
        totalEligibleRate: 0.4,
        totalEligible: 400,
        winRate: 0.3,
        totalWins: 300,
    };

    const mockedDailyStats: BidInsightsDailyStats[] = [
        {
            date: new Date(),
            totalEligibleRate: 0.4,
            totalEligible: 400,
            winRate: 0.3,
            totalWins: 300,
            impressions: 100,
        },
    ];

    beforeEach(() => {
        endpointStub = jasmine.createSpyObj(BidInsightsEndpoint.name, [
            'getBidInsights',
            'getDailyStats',
        ]);

        service = new BidInsightsService(endpointStub);
        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should correctly get bid insights', () => {
        endpointStub.getBidInsights.and
            .returnValue(of(mockedBidInsights, asapScheduler))
            .calls.reset();

        service
            .getBidInsights(adGroupId, date, date, requestStateUpdater)
            .subscribe(bidInsights => {
                expect(bidInsights).toEqual(mockedBidInsights);
            });

        expect(endpointStub.getBidInsights).toHaveBeenCalledTimes(1);
        expect(endpointStub.getBidInsights).toHaveBeenCalledWith(
            adGroupId,
            date,
            date,
            requestStateUpdater
        );
    });

    it('should correctly get bid insights daily stats', () => {
        endpointStub.getDailyStats.and
            .returnValue(of(mockedDailyStats, asapScheduler))
            .calls.reset();

        service
            .getDailyStats(adGroupId, requestStateUpdater)
            .subscribe(dailyStats => {
                expect(dailyStats).toEqual(mockedDailyStats);
            });

        expect(endpointStub.getDailyStats).toHaveBeenCalledTimes(1);
        expect(endpointStub.getDailyStats).toHaveBeenCalledWith(
            adGroupId,
            requestStateUpdater
        );
    });
});
