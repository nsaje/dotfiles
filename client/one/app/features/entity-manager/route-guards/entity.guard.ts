import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {RoutePathName, LevelParam, EntityType} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {ENTITY_MANAGER_CONFIG} from '../entity-manager.config';

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
            if (state.url.includes(RoutePathName.NEW_ENTITY_ANALYTICS_MOCK)) {
                return resolve(true);
            }

            const entityId: string = route.queryParamMap.get(
                ENTITY_MANAGER_CONFIG.idQueryParam
            );
            if (!commonHelpers.isDefined(entityId)) {
                return resolve(true);
            }

            const entityType: EntityType =
                route.queryParams[ENTITY_MANAGER_CONFIG.typeQueryParam];
            if (!commonHelpers.isDefined(entityType)) {
                return resolve(true);
            }

            const entityGetter = this.getEntityGetter(entityType);
            if (!commonHelpers.isDefined(entityGetter)) {
                return resolve(true);
            }

            entityGetter(entityId)
                .then((data: any) => {
                    switch (entityType) {
                        case EntityType.ACCOUNT:
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
                        case EntityType.CAMPAIGN:
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
                        case EntityType.AD_GROUP:
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

    private getEntityGetter(entityType: EntityType) {
        switch (entityType) {
            case EntityType.ACCOUNT:
                return this.zemNavigationService.getAccount;
            case EntityType.CAMPAIGN:
                return this.zemNavigationService.getCampaign;
            case EntityType.AD_GROUP:
                return this.zemNavigationService.getAdGroup;
        }
    }
}
