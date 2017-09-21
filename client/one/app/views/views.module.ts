import {NgModule} from '@angular/core';

import {InventoryPlanningModule} from '../features/inventory-planning/inventory-planning.module';
import {InventoryPlanningViewComponent} from './inventory-planning/inventory-planning.view';

@NgModule({
    imports: [
        InventoryPlanningModule,
    ],
    declarations: [
        InventoryPlanningViewComponent,
    ],
    exports: [
        InventoryPlanningViewComponent,
    ],
    entryComponents: [
        InventoryPlanningViewComponent,
    ],
})
export class ViewsModule {}
