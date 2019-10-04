import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {RulesLibraryModule} from '../rules-library/rules-library.module';
import {EditableCellComponent} from './components/stats-table/editable-cell/editable-cell.component';
import {BidModifierCellComponent} from './components/stats-table/bid-modifier-cell/bid-modifier-cell.component';
import {BidModifierActionsComponent} from './components/bid-modifier-actions/bid-modifier-actions.component';
import {BidModifierImportFormComponent} from './components/bid-modifier-import-form/bid-modifier-import-form.component';
import {RuleActionsComponent} from './components/rule-actions/rule-actions.component';
import {AttributionColumnPickerComponent} from './components/attribution-column-picker/attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from './components/attribution-lookback-window-picker/attribution-lookback-window-picker.component';

@NgModule({
    declarations: [
        EditableCellComponent,
        BidModifierCellComponent,
        BidModifierActionsComponent,
        BidModifierImportFormComponent,
        RuleActionsComponent,
        AttributionColumnPickerComponent,
        AttributionLoockbackWindowPickerComponent,
    ],
    imports: [SharedModule, RulesLibraryModule],
    entryComponents: [
        BidModifierCellComponent,
        BidModifierActionsComponent,
        RuleActionsComponent,
        AttributionColumnPickerComponent,
    ],
})
export class AnalyticsModule {}
