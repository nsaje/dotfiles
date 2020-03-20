import './campaign-budgets-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    TemplateRef,
    Output,
    EventEmitter,
} from '@angular/core';
import * as moment from 'moment';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Currency, Unit} from '../../../../app.constants';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';
import {FormattedCampaignBudget} from '../../types/formatted-campaign-budget';
import {CampaignBudgetErrors} from '../../types/campaign-budget-errors';
import {Credit} from '../../../../core/entities/types/common/credit';

@Component({
    selector: 'zem-campaign-budgets-list',
    templateUrl: './campaign-budgets-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetsListComponent implements OnChanges {
    @Input()
    budgets: CampaignBudget[];
    @Input()
    budgetsErrors: CampaignBudgetErrors[] = [];
    @Input()
    currency: Currency;
    @Input()
    showLicenseFee: boolean;
    @Input()
    showMargin: boolean;
    @Input()
    isEditingEnabled: boolean = false;
    @Input()
    credits: Credit[];
    @Input()
    editFormTemplate: TemplateRef<any>;
    @Output()
    budgetDelete = new EventEmitter<CampaignBudget>();
    @Output()
    budgetEditFormClose = new EventEmitter<void>();

    formattedBudgets: FormattedCampaignBudget[];
    isAnyBudgetEditable: boolean;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.budgets || changes.currency) {
            this.isAnyBudgetEditable = false;
            this.formattedBudgets = this.getFormattedBudgets(this.budgets);
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
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

    hasError(index: number): boolean {
        if (this.budgetsErrors.length > 0) {
            const budgetErrors = (this.budgetsErrors || [])[index];
            if (
                commonHelpers.isDefined(budgetErrors) &&
                Object.keys(budgetErrors).length > 0
            ) {
                return true;
            }
        }
        return false;
    }

    deleteBudget(index: number) {
        this.budgetDelete.emit(this.budgets[index]);
    }

    toggleBudgetEditForm(budgetRow: {isExpanded: boolean}) {
        budgetRow.isExpanded = !budgetRow.isExpanded;
        if (!budgetRow.isExpanded) {
            this.budgetEditFormClose.emit();
        }
    }

    private getFormattedBudgets(
        budgets: CampaignBudget[]
    ): FormattedCampaignBudget[] {
        const formattedBudgets: FormattedCampaignBudget[] = [];
        budgets.forEach(budget => {
            if (this.isBudgetEditable(budget)) {
                this.isAnyBudgetEditable = true;
            }
            formattedBudgets.push({
                ...budget,
                startDate: commonHelpers.isDefined(budget.startDate)
                    ? moment(budget.startDate).format('MM/DD/YYYY')
                    : 'N/A',
                endDate: commonHelpers.isDefined(budget.endDate)
                    ? moment(budget.endDate).format('MM/DD/YYYY')
                    : 'N/A',
                createdDt: commonHelpers.isDefined(budget.createdDt)
                    ? moment(budget.createdDt).format('MM/DD/YYYY')
                    : 'N/A',
                amount: commonHelpers.isDefined(budget.amount)
                    ? currencyHelpers.getValueInCurrency(
                          budget.amount,
                          this.currency
                      )
                    : 'N/A',
                available: commonHelpers.isDefined(budget.available)
                    ? currencyHelpers.getValueInCurrency(
                          budget.available,
                          this.currency
                      )
                    : 'N/A',
                spend: commonHelpers.isDefined(budget.spend)
                    ? currencyHelpers.getValueInCurrency(
                          budget.spend,
                          this.currency
                      )
                    : 'N/A',
                margin: commonHelpers.isDefined(budget.margin)
                    ? `${budget.margin}${unitsHelpers.getUnitText(
                          Unit.Percent
                      )}`
                    : 'N/A',
                licenseFee: commonHelpers.isDefined(budget.licenseFee)
                    ? `${budget.licenseFee}${unitsHelpers.getUnitText(
                          Unit.Percent
                      )}`
                    : 'N/A',
            });
        });
        return formattedBudgets;
    }
}
