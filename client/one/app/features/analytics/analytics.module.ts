import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {RulesLibraryModule} from '../rules-library/rules-library.module';
import {EditableCellComponent} from './components/grid/cells/editable-cell/editable-cell.component';
import {BidModifierCellComponent} from './components/grid/cells/bid-modifiers/bid-modifier-cell/bid-modifier-cell.component';
import {BidModifierActionsComponent} from './components/grid/actions/bid-modifiers/bid-modifier-actions/bid-modifier-actions.component';
import {BidModifierImportFormComponent} from './components/grid/actions/bid-modifiers/bid-modifier-import-form/bid-modifier-import-form.component';
import {RuleActionsComponent} from './components/grid/actions/rule-actions/rule-actions.component';
import {AttributionColumnPickerComponent} from './components/grid/column-selectors/attribution/attribution-column-picker/attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from './components/grid/column-selectors/attribution/attribution-lookback-window-picker/attribution-lookback-window-picker.component';
import {NativeAdPreviewComponent} from './components/grid/shared/thumbnail/native-ad-preview/native-ad-preview.component';
import {DisplayAdPreviewComponent} from './components/grid/shared/thumbnail/display-ad-preview/display-ad-preview.component';
import {CampaignCloningFormComponent} from './components/grid/shared/campaign-cloning-form/campaign-cloning-form.component';
import {BidRangeInfoComponent} from './components/grid/cells/bid-modifiers/bid-range-info/bid-range-info.component';
import {ChartComponent} from './components/chart/chart.component';
import {InfoboxComponent} from './components/infobox/infobox.component';
import {GridContainerComponent} from './components/grid/grid-container/grid-container.component';
import {AnalyticsView} from './views/analytics/analytics.view';
import {CanActivateBreakdownGuard} from './route-guards/canActivateBreakdown.guard';
import {CanActivateEntityGuard} from './route-guards/canActivateEntity.guard';
import {BulkBlacklistActionsComponent} from './components/grid/actions/bulk-blacklist-actions/bulk-blacklist-actions.component';

@NgModule({
    declarations: [
        EditableCellComponent,
        BidModifierCellComponent,
        BidModifierActionsComponent,
        BidModifierImportFormComponent,
        RuleActionsComponent,
        AttributionColumnPickerComponent,
        AttributionLoockbackWindowPickerComponent,
        NativeAdPreviewComponent,
        DisplayAdPreviewComponent,
        CampaignCloningFormComponent,
        BidRangeInfoComponent,
        ChartComponent,
        InfoboxComponent,
        GridContainerComponent,
        AnalyticsView,
        BulkBlacklistActionsComponent,
    ],
    imports: [SharedModule, RulesLibraryModule],
    providers: [CanActivateEntityGuard, CanActivateBreakdownGuard],
    entryComponents: [
        BidModifierCellComponent,
        BidModifierActionsComponent,
        RuleActionsComponent,
        AttributionColumnPickerComponent,
        NativeAdPreviewComponent,
        DisplayAdPreviewComponent,
        CampaignCloningFormComponent,
        AnalyticsView,
        BulkBlacklistActionsComponent,
    ],
})
export class AnalyticsModule {}
