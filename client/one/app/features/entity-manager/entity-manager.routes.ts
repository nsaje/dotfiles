import {Routes} from '@angular/router';
import {EntitySettingsRouterOutlet} from './router-outlets/entity-settings/entity-settings.router-outlet';
import {ENTITY_MANAGER_CONFIG} from './entity-manager.config';
import {CanActivateEntityGuard} from './route-guards/entity.guard';

export const ENTITY_MANAGER_ROUTES: Routes = [
    {
        path: ENTITY_MANAGER_CONFIG.outletName,
        outlet: 'drawer',
        canActivate: [CanActivateEntityGuard],
        component: EntitySettingsRouterOutlet,
    },
];
