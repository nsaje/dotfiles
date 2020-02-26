import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {RoutePathName} from '../app.constants';

@Injectable()
export class CanActivateDashboardGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemNavigationService') private zemNavigationService: any
    ) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.zemNavigationService.getAccountsAccess().then((data: any) => {
                if (data.hasAccounts) {
                    return resolve(true);
                } else {
                    this.router.navigate([RoutePathName.ERROR_FORBIDDEN]);
                    return resolve(false);
                }
            });
        });
    }
}
