import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {EditableCellComponent} from './components/stats-table/editable-cell/editable-cell.component';
import {BidModifierCellComponent} from './components/stats-table/bid-modifier-cell/bid-modifier-cell.component';

const EXPORTED_DECLARATIONS = [EditableCellComponent, BidModifierCellComponent];

@NgModule({
    imports: [SharedModule],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
    entryComponents: [BidModifierCellComponent],
})
export class AnalyticsModule {}
