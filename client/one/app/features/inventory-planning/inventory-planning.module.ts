import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {InventoryPlanningComponent} from './inventory-planning.component';
import {InventoryPlanningFilterComponent} from './components/inventory-planning-filter.component';
import {InventoryPlanningSummaryComponent} from './components/inventory-planning-summary.component';
import {InventoryPlanningBreakdownComponent} from './components/inventory-planning-breakdown.component';

@NgModule({
    imports: [
        SharedModule,
    ],
    declarations: [
        InventoryPlanningComponent,
        InventoryPlanningFilterComponent,
        InventoryPlanningSummaryComponent,
        InventoryPlanningBreakdownComponent,
    ],
    exports: [
        InventoryPlanningComponent,
    ],
})
export class InventoryPlanningModule {}
