import {ICellRendererParams} from 'ag-grid-community';

export interface CurrencyRefundRendererParams extends ICellRendererParams {
    getRefundValueFormatted: (params: CurrencyRefundRendererParams) => string;
}
