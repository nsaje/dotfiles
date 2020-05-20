import './credits-totals.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    OnChanges,
} from '@angular/core';
import {CreditTotal} from '../../../../core/credits/types/credit-total';
import {FormattedCreditTotal} from '../../types/formatted-credit-total';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';

@Component({
    selector: 'zem-credits-totals',
    templateUrl: './credits-totals.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditsTotalsComponent implements OnChanges {
    @Input()
    creditTotals: CreditTotal[];

    formattedCreditTotals: FormattedCreditTotal[] = [];

    ngOnChanges() {
        this.formattedCreditTotals = this.getFormattedCreditTotals(
            this.creditTotals
        );
    }

    private getFormattedCreditTotals(
        creditTotals: CreditTotal[]
    ): FormattedCreditTotal[] {
        const formattedCreditTotals: FormattedCreditTotal[] = [];
        creditTotals.forEach(creditTotal => {
            formattedCreditTotals.push({
                total: isDefined(creditTotal.total)
                    ? getValueInCurrency(
                          creditTotal.total,
                          creditTotal.currency
                      )
                    : 'N/A',
                allocated: isDefined(creditTotal.allocated)
                    ? getValueInCurrency(
                          creditTotal.allocated,
                          creditTotal.currency
                      )
                    : 'N/A',
                past: isDefined(creditTotal.past)
                    ? getValueInCurrency(creditTotal.past, creditTotal.currency)
                    : 'N/A',
                available: isDefined(creditTotal.available)
                    ? getValueInCurrency(
                          creditTotal.available,
                          creditTotal.currency
                      )
                    : 'N/A',
            });
        });
        return formattedCreditTotals;
    }
}
