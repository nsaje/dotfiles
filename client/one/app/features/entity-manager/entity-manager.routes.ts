import {Routes} from '@angular/router';
import {EntitySettingsRouterOutlet} from './router-outlets/entity-settings/entity-settings.router-outlet';
import {ENTITY_MANAGER_CONFIG} from './entity-manager.config';
import {CanActivateEntitySettingsGuard} from './route-guards/canActivateEntitySettings.guard';

export const ENTITY_MANAGER_ROUTES: Routes = [
    {
        path: ENTITY_MANAGER_CONFIG.outletName,
        outlet: 'drawer',
        canActivate: [CanActivateEntitySettingsGuard],
        component: EntitySettingsRouterOutlet,
    },
];
