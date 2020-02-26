import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {RoutePathName, LevelParam, Level} from '../app.constants';
import * as commonHelpers from '../shared/helpers/common.helpers';

@Injectable()
export class CanActivateRedirectGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemNavigationService') private zemNavigationService: any
    ) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            if (commonHelpers.isDefined(route.firstChild)) {
                return resolve(true);
            }

            if (route.routeConfig.path !== RoutePathName.APP_BASE) {
                return resolve(true);
            }

            this.zemNavigationService.getAccountsAccess().then((data: any) => {
                if (data.accountsCount > 1) {
                    this.router.navigate([
                        RoutePathName.APP_BASE,
                        RoutePathName.ANALYTICS,
                        LevelParam.ACCOUNTS,
                    ]);
                    return resolve(false);
                } else {
                    this.router.navigate([
                        RoutePathName.APP_BASE,
                        RoutePathName.ANALYTICS,
                        LevelParam.ACCOUNT,
                        data.defaultAccountId,
                    ]);
                    return resolve(false);
                }
            });
        });
    }
}
