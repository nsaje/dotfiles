import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {InventoryPlanningView} from './views/inventory-planning/inventory-planning.view';
import {
    InventoryPlanningFilterComponent
} from './components/inventory-planning-filter/inventory-planning-filter.component';
import {
    InventoryPlanningSummaryComponent
} from './components/inventory-planning-summary/inventory-planning-summary.component';
import {
    InventoryPlanningBreakdownComponent
} from './components/inventory-planning-breakdown/inventory-planning-breakdown.component';

@NgModule({
    declarations: [
        InventoryPlanningView,
        InventoryPlanningFilterComponent,
        InventoryPlanningSummaryComponent,
        InventoryPlanningBreakdownComponent,
    ],
    imports: [
        SharedModule,
    ],
    entryComponents: [
        InventoryPlanningView,
    ],
})
export class InventoryPlanningModule {}
