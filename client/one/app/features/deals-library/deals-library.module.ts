import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DealsLibraryView} from './views/deals-library/deals-library.view';
import {DealActionsCellComponent} from './components/deal-actions-cell/deal-actions-cell.component';

@NgModule({
    declarations: [DealsLibraryView, DealActionsCellComponent],
    imports: [SharedModule],
    entryComponents: [DealsLibraryView, DealActionsCellComponent],
})
export class DealsLibraryModule {}
