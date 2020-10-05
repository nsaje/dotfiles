import {Injectable} from '@angular/core';
import {
    ActivatedRouteSnapshot,
    CanActivate,
    Router,
    RouterStateSnapshot,
} from '@angular/router';
import {BreakdownParam} from '../../../app.constants';
import {AuthStore} from '../../../core/auth/services/auth.store';

@Injectable()
export class CanActivateBreakdownGuard implements CanActivate {
    constructor(private router: Router, private authStore: AuthStore) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): boolean {
        if (!route.data.breakdowns.includes(route.params.breakdown)) {
            const parentUrl = this.getParentUrl(route, state);
            this.router.navigate([parentUrl]);
            return false;
        }

        if (route.params.breakdown === BreakdownParam.BROWSER) {
            return this.authStore.hasPermission(
                'zemauth.can_see_browser_reporting'
            );
        }

        if (route.params.breakdown === BreakdownParam.CONNECTION_TYPE) {
            return this.authStore.hasPermission(
                'zemauth.can_see_connection_type_reporting'
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
