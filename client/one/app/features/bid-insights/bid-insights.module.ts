import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {SharedModule} from '../../shared/shared.module';
import {BID_INSIGHTS_ROUTES} from './bid-insights.routes';
import {BidInsightsRouterOutlet} from './router-outlets/bid-insights/bid-insights.router-outlet';
import {BidInsightsView} from './views/bid-insights/bid-insights.view';

@NgModule({
    declarations: [BidInsightsRouterOutlet, BidInsightsView],
    imports: [SharedModule, RouterModule.forChild(BID_INSIGHTS_ROUTES)],
    providers: [],
    entryComponents: [BidInsightsRouterOutlet],
})
export class BidInsightsModule {}
