import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {RoutePathName, LevelParam} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class CanActivateEntityGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemNavigationService') private zemNavigationService: any
    ) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const levelParam: LevelParam = route.data.level;
            if (!commonHelpers.isDefined(levelParam)) {
                return resolve(true);
            }

            const entityId = route.paramMap.get('id');
            if (!commonHelpers.isDefined(entityId)) {
                return resolve(true);
            }

            const entityGetter = this.getEntityGetter(levelParam);
            if (!commonHelpers.isDefined(entityGetter)) {
                return resolve(true);
            }

            entityGetter(entityId)
                .then((data: any) => {
                    switch (levelParam) {
                        case LevelParam.ACCOUNT:
                            if (data.account.archived) {
                                this.router.navigate([
                                    RoutePathName.APP_BASE,
                                    RoutePathName.ARCHIVED,
                                    LevelParam.ACCOUNT,
                                    data.account.id,
                                ]);
                                return resolve(false);
                            }
                            break;
                        case LevelParam.CAMPAIGN:
                            if (data.campaign.archived) {
                                this.router.navigate([
                                    RoutePathName.APP_BASE,
                                    RoutePathName.ARCHIVED,
                                    LevelParam.CAMPAIGN,
                                    data.campaign.id,
                                ]);
                                return resolve(false);
                            }
                            break;
                        case LevelParam.AD_GROUP:
                            if (data.adGroup.archived) {
                                this.router.navigate([
                                    RoutePathName.APP_BASE,
                                    RoutePathName.ARCHIVED,
                                    LevelParam.AD_GROUP,
                                    data.adGroup.id,
                                ]);
                                return resolve(false);
                            }
                            break;
                    }
                    return resolve(true);
                })
                .catch(() => {
                    this.router.navigate([
                        RoutePathName.APP_BASE,
                        RoutePathName.ANALYTICS,
                        LevelParam.ACCOUNTS,
                    ]);
                    return resolve(false);
                });
        });
    }

    private getEntityGetter(levelParam: LevelParam) {
        switch (levelParam) {
            case LevelParam.ACCOUNT:
                return this.zemNavigationService.getAccount;
            case LevelParam.CAMPAIGN:
                return this.zemNavigationService.getCampaign;
            case LevelParam.AD_GROUP:
                return this.zemNavigationService.getAdGroup;
        }
    }
}
