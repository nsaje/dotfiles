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
import {NativeAdPreviewComponent} from './components/native-ad-preview/native-ad-preview.component';
import {DisplayAdPreviewComponent} from './components/display-ad-preview/display-ad-preview.component';
import {CampaignCloningFormComponent} from './components/campaign-cloning-form/campaign-cloning-form.component';
import {BidRangeInfoComponent} from './components/stats-table/bid-range-info/bid-range-info.component';
import {ChartComponent} from './components/chart/chart.component';
import {InfoboxComponent} from './components/infobox/infobox.component';
import {GridContainerComponent} from './components/grid-container/grid-container.component';
import {AnalyticsView} from './views/analytics/analytics.view';
import {ArchivedEntityComponent} from './components/archived-entity/archived-entity.component';
import {ArchivedView} from './views/archived/archived.view';
import {NewEntityAnalyticsMockView} from './views/new-entity-analytics-mock/new-entity-analytics-mock.view';

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
        ArchivedEntityComponent,
        AnalyticsView,
        ArchivedView,
        NewEntityAnalyticsMockView,
    ],
    imports: [SharedModule, RulesLibraryModule],
    entryComponents: [
        BidModifierCellComponent,
        BidModifierActionsComponent,
        RuleActionsComponent,
        AttributionColumnPickerComponent,
        NativeAdPreviewComponent,
        DisplayAdPreviewComponent,
        CampaignCloningFormComponent,
        AnalyticsView,
        ArchivedView,
        NewEntityAnalyticsMockView,
    ],
})
export class AnalyticsModule {}
