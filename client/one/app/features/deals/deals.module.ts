import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DealsView} from './views/deals/deals.view';
import {DealActionsCellComponent} from './components/deal-actions-cell/deal-actions-cell.component';
import {ConnectionsListComponent} from './components/connections-list/connections-list.component';
import {DealsActionsComponent} from './components/deals-actions/deals-actions.component';

@NgModule({
    declarations: [
        DealsView,
        DealActionsCellComponent,
        ConnectionsListComponent,
        DealsActionsComponent,
    ],
    imports: [SharedModule],
    entryComponents: [DealsView, DealActionsCellComponent],
})
export class DealsModule {}
