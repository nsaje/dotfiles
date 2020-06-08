import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {CreditsLegacyView} from './views/credits-legacy/credits-legacy.view';
import {CreditsView} from './views/credits/credits.view';
import {CreditsComponent} from './components/credits/credits.component';
import {CreditsScopeSelectorComponent} from './components/credits-scope-selector/credits-scope-selector.component';
import {CreditsTotalsComponent} from './components/credits-totals/credits-totals.component';
import {CreditEditFormComponent} from './components/credit-edit-form/credit-edit-form.component';
import {CampaignBudgetsGridComponent} from './components/campaign-budgets-grid/campaign-budgets-grid.component';
import {CreditsGridComponent} from './components/credits-grid/credits-grid.component';
import {CreditActionsCellComponent} from './components/credits-grid/components/credit-actions-cell/credit-actions-cell.component';
import {RefundActionsCellComponent} from './components/credits-grid/components/refund-actions-cell/refund-actions-cell.component';
import {RefundFormComponent} from './components/refund-form/refund-form.component';

@NgModule({
    declarations: [
        CreditsLegacyView,
        CreditsView,
        CreditsComponent,
        CreditsScopeSelectorComponent,
        CreditsTotalsComponent,
        CreditEditFormComponent,
        CampaignBudgetsGridComponent,
        CreditsGridComponent,
        CreditActionsCellComponent,
        RefundActionsCellComponent,
        RefundFormComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        CreditsLegacyView,
        CreditsView,
        CreditsScopeSelectorComponent,
        CreditActionsCellComponent,
        RefundActionsCellComponent,
    ],
})
export class CreditsModule {}
