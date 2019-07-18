import './campaign-budgets-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import * as moment from 'moment';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Currency} from '../../../../app.constants';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';
import {FormattedCampaignBudget} from '../../types/formatted-campaign-budget';

@Component({
    selector: 'zem-campaign-budgets-list',
    templateUrl: './campaign-budgets-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetsListComponent implements OnChanges {
    @Input()
    budgets: CampaignBudget[];
    @Input()
    currency: Currency;
    @Input()
    showLicenseFee: boolean;
    @Input()
    showMargin: boolean;
    @Input()
    isEditingEnabled: boolean;

    formattedBudgets: FormattedCampaignBudget[];
    isAnyBudgetEditable: boolean;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.budgets || changes.currency) {
            this.isAnyBudgetEditable = false;
            this.formattedBudgets = [];
            this.budgets.forEach(budget => {
                if (this.isBudgetEditable(budget)) {
                    this.isAnyBudgetEditable = true;
                }
                this.formattedBudgets.push({
                    ...budget,
                    startDate: moment(budget.startDate).format('MM/DD/YYYY'),
                    endDate: moment(budget.endDate).format('MM/DD/YYYY'),
                    createdDt: moment(budget.createdDt).format('MM/DD/YYYY'),
                    amount: currencyHelpers.getValueInCurrency(
                        budget.amount,
                        this.currency
                    ),
                    available: currencyHelpers.getValueInCurrency(
                        budget.available,
                        this.currency
                    ),
                    spend: currencyHelpers.getValueInCurrency(
                        budget.spend,
                        this.currency
                    ),
                    margin: currencyHelpers.getValueInCurrency(
                        budget.margin,
                        this.currency
                    ),
                    licenseFee: currencyHelpers.getValueInCurrency(
                        budget.licenseFee,
                        this.currency
                    ),
                });
            });
        }
    }

    isBudgetEditable(
        budget: CampaignBudget | FormattedCampaignBudget
    ): boolean {
        return (
            this.isEditingEnabled &&
            (budget.canEditStartDate ||
                budget.canEditEndDate ||
                budget.canEditAmount)
        );
    }
}
