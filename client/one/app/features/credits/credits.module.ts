import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {CreditsView} from './views/credits/credits.view';
import {CreditsTotalsComponent} from './components/credits-totals/credits-totals.component';
import {CreditEditFormComponent} from './components/credit-edit-form/credit-edit-form.component';
import {CampaignBudgetsGridComponent} from './components/campaign-budgets-grid/campaign-budgets-grid.component';
import {CreditsGridComponent} from './components/credits-grid/credits-grid.component';
import {CreditActionsCellComponent} from './components/credits-grid/components/credit-actions-cell/credit-actions-cell.component';
import {RefundActionsCellComponent} from './components/credits-grid/components/refund-actions-cell/refund-actions-cell.component';
import {RefundFormComponent} from './components/refund-form/refund-form.component';
import {RefundsGridComponent} from './components/refunds-grid/refunds-grid.component';

@NgModule({
    declarations: [
        CreditsView,
        CreditsTotalsComponent,
        CreditEditFormComponent,
        CampaignBudgetsGridComponent,
        CreditsGridComponent,
        CreditActionsCellComponent,
        RefundActionsCellComponent,
        RefundFormComponent,
        RefundsGridComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        CreditsView,
        CreditActionsCellComponent,
        RefundActionsCellComponent,
    ],
})
export class CreditsModule {}
