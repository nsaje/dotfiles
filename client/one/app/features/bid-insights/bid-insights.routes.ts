import {Routes} from '@angular/router';
import {BidInsightsRouterOutlet} from './router-outlets/bid-insights/bid-insights.router-outlet';
import {BID_INSIGHTS_CONFIG} from './bid-insights.config';
import {CanActivatePermissionGuard} from '../../route-guards/canActivatePermission.guard';

export const BID_INSIGHTS_ROUTES: Routes = [
    {
        path: BID_INSIGHTS_CONFIG.outletName,
        outlet: 'drawer',
        component: BidInsightsRouterOutlet,
        canActivate: [CanActivatePermissionGuard],
        data: {permissions: ['zemauth.can_see_bid_insights']},
    },
];
