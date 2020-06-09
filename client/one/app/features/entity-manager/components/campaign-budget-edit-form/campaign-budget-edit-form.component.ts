import './campaign-budget-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Currency, Unit} from '../../../../app.constants';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';
import {CampaignBudgetErrors} from '../../types/campaign-budget-errors';
import * as moment from 'moment';
import {Credit} from '../../../../core/credits/types/credit';
import {FormattedCredit} from '../../types/formatted-credit';

@Component({
    selector: 'zem-campaign-budget-edit-form',
    templateUrl: './campaign-budget-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetEditFormComponent implements OnChanges {
    @Input()
    budget: CampaignBudget;
    @Input()
    currency: Currency;
    @Input()
    budgetErrors: CampaignBudgetErrors;
    @Input()
    showLicenseFee: boolean;
    @Input()
    showMargin: boolean;
    @Input()
    credits: Credit[];
    @Output()
    budgetChange = new EventEmitter<ChangeEvent<CampaignBudget>>();

    formattedCredits: FormattedCredit[] = [];
    createdDate: string;
    currencySymbol: string;
    minDate: Date;
    maxDate: Date;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.budget) {
            if (this.budget.createdDt) {
                this.createdDate = moment(this.budget.createdDt).format(
                    'MM/DD/YYYY'
                );
            }
            if (this.budget.creditId) {
                const credit = this.credits.find(item => {
                    return item.id === this.budget.creditId;
                });
                if (commonHelpers.isDefined(credit)) {
                    this.minDate = credit.startDate;
                    this.maxDate = credit.endDate;
                }
            }
        }
        if (changes.credits || changes.currency) {
            this.currencySymbol = currencyHelpers.getCurrencySymbol(
                this.currency
            );
            this.formattedCredits = this.getFormattedCredits(this.credits);
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    onCreditIdSelected(creditId: string) {
        const selectedCredit = this.credits.find(item => {
            return item.id === creditId;
        });
        const todayDate = moment().toDate();
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                creditId: creditId,
                startDate:
                    selectedCredit.startDate > todayDate
                        ? selectedCredit.startDate
                        : todayDate,
                endDate: null,
            },
        });
    }

    onStartDateChange($event: Date) {
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                startDate: $event,
            },
        });
    }

    onEndDateChange($event: Date) {
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                endDate: $event,
            },
        });
    }

    onAmountChange($event: string) {
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                amount: $event,
            },
        });
    }

    onMarginChange($event: string) {
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                margin: $event,
            },
        });
    }

    onCommentChange($event: string) {
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                comment: $event,
            },
        });
    }

    private getFormattedCredits(credits: Credit[]): FormattedCredit[] {
        const formattedCredits: FormattedCredit[] = [];
        credits.forEach(credit => {
            if (
                (!commonHelpers.isDefined(this.budget.id) &&
                    credit.isAvailable) ||
                (commonHelpers.isDefined(this.budget.id) &&
                    this.budget.creditId === credit.id)
            ) {
                formattedCredits.push({
                    ...credit,
                    createdOn: commonHelpers.isDefined(credit.createdOn)
                        ? moment(credit.createdOn).format('MM/DD/YYYY')
                        : 'N/A',
                    startDate: commonHelpers.isDefined(credit.startDate)
                        ? moment(credit.startDate).format('MM/DD/YYYY')
                        : 'N/A',
                    endDate: commonHelpers.isDefined(credit.endDate)
                        ? moment(credit.endDate).format('MM/DD/YYYY')
                        : 'N/A',
                    total: commonHelpers.isDefined(credit.total)
                        ? currencyHelpers.getValueInCurrency(
                              credit.total,
                              this.currency
                          )
                        : 'N/A',
                    allocated: commonHelpers.isDefined(credit.allocated)
                        ? currencyHelpers.getValueInCurrency(
                              credit.allocated,
                              this.currency
                          )
                        : 'N/A',
                    available: commonHelpers.isDefined(credit.available)
                        ? currencyHelpers.getValueInCurrency(
                              credit.available,
                              this.currency
                          )
                        : 'N/A',
                    licenseFee: commonHelpers.isDefined(credit.licenseFee)
                        ? `${credit.licenseFee}${unitsHelpers.getUnitText(
                              Unit.Percent
                          )}`
                        : 'N/A',
                });
            }
        });
        return formattedCredits;
    }
}
