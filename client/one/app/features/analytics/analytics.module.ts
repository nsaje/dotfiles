import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {RulesModule} from '../rules/rules.module';
import {EditableCellComponent} from './components/grid/cells/editable-cell/editable-cell.component';
import {BidModifierCellComponent} from './components/grid/cells/bid-modifiers/bid-modifier-cell/bid-modifier-cell.component';
import {BidModifierActionsComponent} from './components/grid/actions/bid-modifiers/bid-modifier-actions/bid-modifier-actions.component';
import {BidModifierImportFormComponent} from './components/grid/actions/bid-modifiers/bid-modifier-import-form/bid-modifier-import-form.component';
import {RuleActionsComponent} from './components/grid/actions/rule-actions/rule-actions.component';
import {AttributionColumnPickerComponent} from './components/grid/column-selectors/attribution/attribution-column-picker/attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from './components/grid/column-selectors/attribution/attribution-lookback-window-picker/attribution-lookback-window-picker.component';
import {NativeAdPreviewComponent} from './components/grid/shared/native-ad-preview/native-ad-preview.component';
import {DisplayAdPreviewComponent} from './components/grid/shared/display-ad-preview/display-ad-preview.component';
import {CampaignCloningFormComponent} from './components/grid/shared/campaign-cloning-form/campaign-cloning-form.component';
import {BidRangeInfoComponent} from './components/grid/cells/bid-modifiers/bid-range-info/bid-range-info.component';
import {ChartComponent} from './components/chart/chart.component';
import {InfoboxComponent} from './components/infobox/infobox.component';
import {GridContainerComponent} from './components/grid/grid-container/grid-container.component';
import {AnalyticsView} from './views/analytics/analytics.view';
import {CanActivateBreakdownGuard} from './route-guards/canActivateBreakdown.guard';
import {CanActivateEntityGuard} from './route-guards/canActivateEntity.guard';
import {BulkBlacklistActionsComponent} from './components/grid/actions/bulk-blacklist-actions/bulk-blacklist-actions.component';
import {AddToPublishersActionComponent} from './components/grid/actions/add-to-publishers/add-to-publishers-action/add-to-publishers-action.component';
import {AddToPublishersFormComponent} from './components/grid/actions/add-to-publishers/add-to-publishers-form/add-to-publishers-form.component';
import {AlertsComponent} from './components/grid/alerts/alerts.component';
import {AlertsStore} from './services/alerts-store/alerts.store';
import {GridBridgeComponent} from './components/grid/grid-bridge/grid-bridge.component';
import {ConversionPixelSelectorComponent} from './components/chart/components/conversion-pixel-selector/conversion-pixel-selector.component';
import {BreakdownCellComponent} from './components/grid/cells/breakdown-cell/breakdown-cell.component';

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
        AddToPublishersActionComponent,
        AddToPublishersFormComponent,
        AlertsComponent,
        GridBridgeComponent,
        ConversionPixelSelectorComponent,
        BreakdownCellComponent,
    ],
    imports: [SharedModule, RulesModule],
    providers: [CanActivateEntityGuard, CanActivateBreakdownGuard, AlertsStore],
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
        AddToPublishersActionComponent,
        GridBridgeComponent,
        ConversionPixelSelectorComponent,
        BreakdownCellComponent,
    ],
})
export class AnalyticsModule {}
