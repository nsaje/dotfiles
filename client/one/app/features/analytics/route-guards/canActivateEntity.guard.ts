import {Injectable, Inject} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
    Router,
} from '@angular/router';
import {
    RoutePathName,
    LevelParam,
    EntityType,
    LEVEL_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class CanActivateEntityGuard implements CanActivate {
    constructor(
        private router: Router,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const levelParam: LevelParam = route.data.level;
            if (!commonHelpers.isDefined(levelParam)) {
                this.router.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNTS,
                ]);
                return resolve(false);
            }

            const entityId = route.paramMap.get('id');
            if (!commonHelpers.isDefined(entityId)) {
                return resolve(true);
            }

            const entityType: EntityType =
                LEVEL_TO_ENTITY_TYPE_MAP[LEVEL_PARAM_TO_LEVEL_MAP[levelParam]];

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
                            levelParam,
                            entityId,
                        ]);
                        return resolve(false);
                    }
                    return resolve(true);
                });
        });
    }
}
