import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {BreakdownParam} from '../../../app.constants';

@Injectable()
export class CanActivateBreakdownGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemPermissions') private zemPermissions: any
    ) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): boolean {
        if (!route.data.breakdowns.includes(route.params.breakdown)) {
            const parentUrl = this.getParentUrl(route, state);
            this.router.navigate([parentUrl]);
            return false;
        }
        if (!this.canSeeBreakdown(route.params.breakdown)) {
            const parentUrl = this.getParentUrl(route, state);
            this.router.navigate([parentUrl]);
            return false;
        }
        return true;
    }

    private canSeeBreakdown(breakdown: BreakdownParam): boolean {
        const isDeliveryBreakdown = [
            BreakdownParam.COUNTRY,
            BreakdownParam.STATE,
            BreakdownParam.DMA,
            BreakdownParam.DEVICE,
            BreakdownParam.ENVIRONMENT,
            BreakdownParam.OPERATING_SYSTEM,
        ].includes(breakdown);
        if (isDeliveryBreakdown) {
            return this.zemPermissions.hasPermission(
                'zemauth.can_see_top_level_delivery_breakdowns'
            );
        }
        return true;
    }

    private getParentUrl(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): string {
        return state.url.slice(
            0,
            state.url.indexOf(route.url[route.url.length - 1].path)
        );
    }
}