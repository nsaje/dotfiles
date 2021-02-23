import {NgModule} from '@angular/core';
import {BidInsightsService} from './services/bid-insights.service';
import {BidInsightsEndpoint} from './services/bid-insights.endpoint';

@NgModule({
    providers: [BidInsightsService, BidInsightsEndpoint],
})
export class BidInsightsModule {}
