import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DealsLibraryView} from './views/deals-library/deals-library.view';
import {DealActionsCellComponent} from './components/deal-actions-cell/deal-actions-cell.component';
import {ConnectionActionsCellComponent} from './components/connection-actions-cell/connection-actions-cell.component';
import {ConnectionsListComponent} from './components/connections-list/connections-list.component';

@NgModule({
    declarations: [
        DealsLibraryView,
        DealActionsCellComponent,
        ConnectionActionsCellComponent,
        ConnectionsListComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        DealsLibraryView,
        DealActionsCellComponent,
        ConnectionActionsCellComponent,
    ],
})
export class DealsLibraryModule {}
