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
import {Currency} from '../../../../app.constants';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';
import * as commonHelper from '../../../../shared/helpers/common.helpers';
import {CampaignBudgetErrors} from '../../types/campaign-budget-errors';
import * as moment from 'moment';
import {AccountCredit} from '../../../../core/entities/types/account/account-credit';
import {FormattedAccountCredit} from '../../types/formatted-account-credit';

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
    accountCredits: AccountCredit[];
    @Output()
    budgetChange = new EventEmitter<ChangeEvent<CampaignBudget>>();

    createdDate: string;
    currencySymbol: string;
    formattedAccountCredits: FormattedAccountCredit[] = [];
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
                const accountCredit = this.accountCredits.find(item => {
                    return item.id === this.budget.creditId;
                });
                if (commonHelper.isDefined(accountCredit)) {
                    this.minDate = accountCredit.startDate;
                    this.maxDate = accountCredit.endDate;
                }
            }
        }
        if (changes.accountCredits || changes.currency) {
            this.currencySymbol = currencyHelpers.getCurrencySymbol(
                this.currency
            );
            this.formattedAccountCredits = this.getFormattedAccountCredits(
                this.accountCredits
            );
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    onCreditIdSelected(creditId: string) {
        const selectedAccountCredit = this.accountCredits.find(item => {
            return item.id === creditId;
        });
        const todayDate = moment().toDate();
        this.budgetChange.emit({
            target: this.budget,
            changes: {
                creditId: creditId,
                startDate:
                    selectedAccountCredit.startDate > todayDate
                        ? selectedAccountCredit.startDate
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

    private getFormattedAccountCredits(
        accountCredits: AccountCredit[]
    ): FormattedAccountCredit[] {
        const formattedAccountCredits: FormattedAccountCredit[] = [];
        accountCredits.forEach(credit => {
            if (
                (!commonHelper.isDefined(this.budget.id) &&
                    credit.isAvailable) ||
                (commonHelper.isDefined(this.budget.id) &&
                    this.budget.creditId === credit.id)
            ) {
                formattedAccountCredits.push({
                    ...credit,
                    createdOn: commonHelper.isDefined(credit.createdOn)
                        ? moment(credit.createdOn).format('MM/DD/YYYY')
                        : 'N/A',
                    startDate: commonHelper.isDefined(credit.startDate)
                        ? moment(credit.startDate).format('MM/DD/YYYY')
                        : 'N/A',
                    endDate: commonHelper.isDefined(credit.endDate)
                        ? moment(credit.endDate).format('MM/DD/YYYY')
                        : 'N/A',
                    total: commonHelper.isDefined(credit.total)
                        ? currencyHelpers.getValueInCurrency(
                              credit.total,
                              this.currency
                          )
                        : 'N/A',
                    allocated: commonHelper.isDefined(credit.allocated)
                        ? currencyHelpers.getValueInCurrency(
                              credit.allocated,
                              this.currency
                          )
                        : 'N/A',
                    available: commonHelper.isDefined(credit.available)
                        ? currencyHelpers.getValueInCurrency(
                              credit.available,
                              this.currency
                          )
                        : 'N/A',
                    licenseFee: commonHelper.isDefined(credit.licenseFee)
                        ? currencyHelpers.getValueInCurrency(
                              credit.licenseFee,
                              this.currency
                          )
                        : 'N/A',
                });
            }
        });
        return formattedAccountCredits;
    }
}
