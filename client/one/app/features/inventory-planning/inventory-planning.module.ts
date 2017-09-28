import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {InventoryPlanningComponent} from './inventory-planning.component';
import {
    InventoryPlanningSummaryComponent
} from './components/inventory-planning-summary/inventory-planning-summary.component';
import {
    InventoryPlanningBreakdownComponent
} from './components/inventory-planning-breakdown/inventory-planning-breakdown.component';
import {
    InventoryPlanningFilterComponent
} from './components/inventory-planning-filter/inventory-planning-filter.component';
import {BigNumberPipe} from './big-number.pipe.ts';

@NgModule({
    imports: [
        SharedModule,
    ],
    declarations: [
        InventoryPlanningComponent,
        InventoryPlanningSummaryComponent,
        InventoryPlanningBreakdownComponent,
        InventoryPlanningFilterComponent,
        BigNumberPipe,
    ],
    exports: [
        InventoryPlanningComponent,
    ],
})
export class InventoryPlanningModule {}
