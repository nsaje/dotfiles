import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {EditableCellComponent} from './components/stats-table/editable-cell/editable-cell.component';
import {BidModifierCellComponent} from './components/stats-table/bid-modifier-cell/bid-modifier-cell.component';
import {BidModifierActionsComponent} from './components/bid-modifier-actions/bid-modifier-actions.component';
import {BidModifierUploadModalComponent} from './components/bid-modifier-actions/bid-modifier-upload-modal/bid-modifier-upload-modal.component';
import {AttributionColumnPickerComponent} from './components/attribution-column-picker/attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from './components/attribution-lookback-window-picker/attribution-lookback-window-picker.component';

const EXPORTED_DECLARATIONS = [
    EditableCellComponent,
    BidModifierCellComponent,
    BidModifierActionsComponent,
    BidModifierUploadModalComponent,
    AttributionColumnPickerComponent,
    AttributionLoockbackWindowPickerComponent,
];

@NgModule({
    imports: [SharedModule],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
    entryComponents: [
        BidModifierCellComponent,
        BidModifierActionsComponent,
        AttributionColumnPickerComponent,
    ],
})
export class AnalyticsModule {}
