import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {
    RoutePathName,
    EntityType,
    ENTITY_TYPE_TO_LEVEL_MAP,
    LEVEL_TO_LEVEL_PARAM_MAP,
    LevelParam,
} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {ENTITY_MANAGER_CONFIG} from '../entity-manager.config';

@Injectable()
export class CanActivateEntitySettingsGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
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
                this.router.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNTS,
                ]);
                return resolve(false);
            }

            const entityType =
                route.queryParams[ENTITY_MANAGER_CONFIG.typeQueryParam];
            if (!this.isValidEntityType(entityType)) {
                this.router.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNTS,
                ]);
                return resolve(false);
            }

            this.zemNavigationNewService
                .getEntityById(entityType, entityId)
                .then((entity: any) => {
                    if (!commonHelpers.isDefined(entity)) {
                        this.router.navigate([
                            RoutePathName.APP_BASE,
                            RoutePathName.ANALYTICS,
                            LevelParam.ACCOUNTS,
                        ]);
                        return resolve(false);
                    }
                    if (
                        commonHelpers.isDefined(entity.data) &&
                        entity.data.archived
                    ) {
                        this.router.navigate([
                            RoutePathName.APP_BASE,
                            RoutePathName.ARCHIVED,
                            LEVEL_TO_LEVEL_PARAM_MAP[
                                ENTITY_TYPE_TO_LEVEL_MAP[entityType]
                            ],
                            entityId,
                        ]);
                        return resolve(false);
                    }
                    return resolve(true);
                });
        });
    }

    private isValidEntityType(entityType: any): boolean {
        const entityTypes: EntityType[] = [
            EntityType.ACCOUNT,
            EntityType.CAMPAIGN,
            EntityType.AD_GROUP,
        ];
        return (
            commonHelpers.isDefined(entityType) &&
            entityTypes.includes(entityType)
        );
    }
}
