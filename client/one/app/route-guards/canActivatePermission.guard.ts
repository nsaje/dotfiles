import {Injectable} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    UrlTree,
    Router,
} from '@angular/router';
import {AuthStore} from '../core/auth/services/auth.store';
import {RoutePathName} from '../app.constants';

@Injectable()
export class CanActivatePermissionGuard implements CanActivate {
    constructor(private authStore: AuthStore, private router: Router) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): boolean | UrlTree {
        return (
            this.authStore.hasPermission(route?.data?.permissions || []) ||
            this.router.createUrlTree([RoutePathName.ERROR_FORBIDDEN])
        );
    }
}
