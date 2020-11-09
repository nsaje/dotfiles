import './currency-refund-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {CurrencyRefundRendererParams} from './types/currency-refund.renderer-params';

@Component({
    templateUrl: './currency-refund-cell.component.html',
})
export class CurrencyRefundCellComponent implements ICellRendererAngularComp {
    params: CurrencyRefundRendererParams;
    valueFormatted: string;
    refundValueFormatted: string;

    agInit(params: CurrencyRefundRendererParams): void {
        this.params = params;
        this.valueFormatted = this.params.valueFormatted;
        this.refundValueFormatted = this.params.getRefundValueFormatted(
            this.params
        );
    }

    refresh(params: CurrencyRefundRendererParams): boolean {
        const valueFormatted = params.valueFormatted;
        if (this.valueFormatted !== valueFormatted) {
            return false;
        }
        return true;
    }
}
