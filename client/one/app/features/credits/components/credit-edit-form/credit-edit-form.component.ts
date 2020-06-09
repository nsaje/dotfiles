import './credit-edit-form.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
    OnInit,
} from '@angular/core';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {CreditsStoreFieldsErrorsState} from '../../services/credits-store/credits.store.fields-errors-state';
import {Credit} from '../../../../core/credits/types/credit';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Currency, CreditStatus} from '../../../../app.constants';
import {CURRENCIES, APP_CONFIG} from '../../../../app.config';
import * as moment from '../../../../../../lib/components/moment/moment';
import * as clone from 'clone';

@Component({
    selector: 'zem-credit-edit-form',
    templateUrl: './credit-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditEditFormComponent implements OnChanges, OnInit {
    @Input()
    credit: Credit;
    @Input()
    isReadOnly: boolean;
    @Input()
    isSigned: boolean;
    @Input()
    showLicenseFee: boolean;
    @Input()
    creditErrors: CreditsStoreFieldsErrorsState;
    @Output()
    creditChange: EventEmitter<ChangeEvent<Credit>> = new EventEmitter<
        ChangeEvent<Credit>
    >();

    defaultLicenseFeeItems: {
        value: string;
        name: string;
    }[] = [
        {value: '15', name: '15%'},
        {value: '20', name: '20%'},
        {value: '25', name: '25%'},
    ];

    licenseFeeItems: {
        value: string;
        name: string;
    }[];

    CURRENCIES = CURRENCIES;
    currencySymbol: string;
    minStartDate: Date;
    minEndDate: Date;

    wasSigned: boolean;
    createdOnDate: string;

    ngOnInit(): void {
        this.wasSigned = this.isSigned;
        this.minStartDate = new Date();
        this.minEndDate = isDefined(this.credit.endDate)
            ? this.credit.endDate
            : new Date();

        if (this.credit.createdOn) {
            this.createdOnDate = moment(this.credit.createdOn).format(
                'MM/DD/YYYY'
            );
        }

        this.licenseFeeItems = this.getLicenseFeeItems(
            this.credit,
            clone(this.defaultLicenseFeeItems)
        );
    }

    ngOnChanges(): void {
        this.currencySymbol = this.credit.currency
            ? APP_CONFIG.currencySymbols[this.credit.currency]
            : Currency.USD;
    }

    onStartDateChange(startDate: Date): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                startDate: startDate,
            },
        });
    }

    onEndDateChange(endDate: Date): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                endDate: endDate,
            },
        });
    }

    onLicenseFeeChange(licenseFee: string): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                licenseFee: licenseFee,
            },
        });
    }

    onCurrencyChange(currency: Currency): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                currency: currency,
            },
        });
    }

    onAmountChange(amount: number): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                amount: amount,
            },
        });
    }

    onCommentChange(comment: string): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                comment: comment,
            },
        });
    }

    onContractIdChange(contractId: string): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                contractId: contractId,
            },
        });
    }

    onContractNumberChange(contractNumber: string): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                contractNumber: contractNumber,
            },
        });
    }

    onSignedToggle(signed: boolean): void {
        this.creditChange.emit({
            target: this.credit,
            changes: {
                status: signed ? CreditStatus.SIGNED : CreditStatus.PENDING,
            },
        });
    }

    addLicenseFeeItem(
        item: string
    ): {
        value: string;
        name: string;
    } {
        return {value: item, name: `${item}%`};
    }

    private getLicenseFeeItems(
        credit: Credit,
        licenseFeeItems: {
            value: string;
            name: string;
        }[]
    ): {
        value: string;
        name: string;
    }[] {
        if (!credit.licenseFee) {
            return licenseFeeItems;
        }

        const itemExists = licenseFeeItems.find(licenseFeeItem => {
            return licenseFeeItem.value === credit.licenseFee;
        });
        if (!itemExists) {
            licenseFeeItems.push({
                value: credit.licenseFee,
                name: `${credit.licenseFee}%`,
            });
        }
        return licenseFeeItems;
    }
}
