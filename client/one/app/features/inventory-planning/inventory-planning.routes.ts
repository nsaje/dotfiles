import {Routes} from '@angular/router';
import {InventoryPlanningView} from './views/inventory-planning/inventory-planning.view';

export const INVENTORY_PLANNING_ROUTES: Routes = [
    {path: '', pathMatch: 'full', component: InventoryPlanningView},
];
