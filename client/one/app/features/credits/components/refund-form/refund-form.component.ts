import './refund-form.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
    OnInit,
} from '@angular/core';
import {
    isDefined,
    getValueOrDefault,
} from '../../../../shared/helpers/common.helpers';
import {CreditsStoreFieldsErrorsState} from '../../services/credits-store/credits.store.fields-errors-state';
import {Credit} from '../../../../core/credits/types/credit';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Currency} from '../../../../app.constants';
import {APP_CONFIG} from '../../../../app.config';
import * as moment from '../../../../../../lib/components/moment/moment';
import {CreditRefund} from '../../../../core/credits/types/credit-refund';
import {Account} from '../../../../core/entities/types/account/account';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import * as clone from 'clone';

@Component({
    selector: 'zem-refund-form',
    templateUrl: './refund-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RefundFormComponent implements OnChanges, OnInit {
    @Input()
    refund: CreditRefund;
    @Input()
    credit: Credit;
    @Input()
    creditScopeState: ScopeSelectorState;
    @Input()
    accounts: Account[];
    @Input()
    isReadOnly: boolean;
    @Input()
    refundErrors: CreditsStoreFieldsErrorsState;
    @Output()
    refundChange: EventEmitter<ChangeEvent<CreditRefund>> = new EventEmitter<
        ChangeEvent<CreditRefund>
    >();

    currencySymbol: string;
    createdOnDate: string;
    minDate: Date;
    maxDate: Date;
    isAccountDisabled: boolean;
    mediaAmount: number = 0;
    formattedTotalRefundedAmount: string;

    ngOnInit(): void {
        const now = moment(Date.now());
        this.minDate = clone(now)
            .subtract(1, 'month')
            .startOf('month')
            .toDate();
        this.maxDate = clone(now)
            .endOf('month')
            .toDate();

        this.isAccountDisabled =
            this.creditScopeState === ScopeSelectorState.ACCOUNT_SCOPE;

        this.currencySymbol = this.credit.currency
            ? APP_CONFIG.currencySymbols[this.credit.currency]
            : Currency.USD;

        if (this.credit.createdOn) {
            this.createdOnDate = moment(this.credit.createdOn).format(
                'MM/DD/YYYY'
            );
        }
    }

    ngOnChanges() {
        this.formattedTotalRefundedAmount = getValueInCurrency(
            `${this.getTotalRefundedAmount(
                this.mediaAmount,
                this.credit.licenseFee,
                this.refund.effectiveMargin
            )}`,
            this.credit.currency
        );
    }

    onStartDateChange(startDate: Date): void {
        this.refundChange.emit({
            target: this.refund,
            changes: {
                startDate: startDate,
            },
        });
    }

    onAccountIdChange(accountId: string): void {
        this.refundChange.emit({
            target: this.refund,
            changes: {
                accountId: accountId,
            },
        });
    }

    onMediaAmountChange(amount: number): void {
        this.mediaAmount = amount;
        this.refundChange.emit({
            target: this.refund,
            changes: {
                amount: this.getTotalRefundedAmount(
                    this.mediaAmount,
                    this.credit.licenseFee,
                    this.refund.effectiveMargin
                ),
            },
        });
    }

    onEffectiveMarginChange(effectiveMargin: string): void {
        this.refundChange.emit({
            target: this.refund,
            changes: {
                effectiveMargin: effectiveMargin,
                amount: this.getTotalRefundedAmount(
                    this.mediaAmount,
                    this.credit.licenseFee,
                    effectiveMargin
                ),
            },
        });
    }

    onCommentChange(comment: string): void {
        this.refundChange.emit({
            target: this.refund,
            changes: {
                comment: comment,
            },
        });
    }

    private getTotalRefundedAmount(
        mediaAmount: number,
        licenseFee: string,
        effectiveMargin: string
    ): number {
        const amount = getValueOrDefault(mediaAmount, 0);
        const creditLicenseFee =
            parseFloat(getValueOrDefault(licenseFee, '0')) / 100;
        const margin =
            parseFloat(getValueOrDefault(effectiveMargin, '0')) / 100;
        return Math.ceil(amount / (1 - creditLicenseFee) / (1 - margin));
    }
}
