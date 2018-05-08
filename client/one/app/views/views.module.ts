import {NgModule} from '@angular/core';

import {InventoryPlanningModule} from '../features/inventory-planning/inventory-planning.module';
import {InventoryPlanningView} from './inventory-planning/inventory-planning.view';

@NgModule({
    imports: [
        InventoryPlanningModule,
    ],
    declarations: [
        InventoryPlanningView,
    ],
    exports: [
        InventoryPlanningView,
    ],
    entryComponents: [
        InventoryPlanningView,
    ],
})
export class ViewsModule {}
