import {ColDef, ICellRendererParams} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {
    SMART_GRID_CELL_CURRENCY_CLASS,
    SMART_GRID_CELL_CURRENCY_REFUND_CLASS,
} from '../../grid-bridge.component.constants';
import {GridRow} from '../../types/grid-row';
import {CurrencyDataCellComponent} from '../../../cells/currency-data-cell/currency-data-cell.component';
import {StatsDataColumnMapper} from './stats-data.mapper';
import {
    REFUND_FIELDS,
    REFUND_PINNED_ROW_CELL_BREAKDOWNS,
    REFUND_ROW_CELL_BREAKDOWNS,
} from '../../grid-bridge.component.config';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {
    formatGridColumnValue,
    FormatGridColumnValueOptions,
} from '../../helpers/grid-bridge.helpers';
import {CurrencyDataRendererParams} from '../../../cells/currency-data-cell/types/currency-data.renderer-params';
import {CurrencyRefundCellComponent} from '../../../cells/currency-refund-cell/currency-refund-cell.component';
import {CurrencyRefundRendererParams} from '../../../cells/currency-refund-cell/types/currency-refund.renderer-params';

export class CurrencyColumnMapper extends StatsDataColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        let colDef: ColDef = super.getColDef(grid, column);

        const refundField = this.getRefundField(column);
        if (
            REFUND_ROW_CELL_BREAKDOWNS.includes(grid.meta.data.breakdown) &&
            REFUND_FIELDS.includes(refundField)
        ) {
            colDef = {
                ...colDef,
                cellClass: SMART_GRID_CELL_CURRENCY_REFUND_CLASS,
                cellRendererFramework: CurrencyRefundCellComponent,
                cellRendererParams: {
                    getRefundValueFormatted: (
                        params: CurrencyRefundRendererParams
                    ) => {
                        return this.getRefundValueFormatted(
                            grid,
                            column,
                            params,
                            refundField
                        );
                    },
                } as CurrencyRefundRendererParams,
            };
        }

        if (
            REFUND_PINNED_ROW_CELL_BREAKDOWNS.includes(
                grid.meta.data.breakdown
            ) &&
            REFUND_FIELDS.includes(refundField)
        ) {
            colDef = {
                ...colDef,
                pinnedRowCellRendererFramework: CurrencyRefundCellComponent,
                pinnedRowCellRendererParams: {
                    getRefundValueFormatted: (
                        params: CurrencyRefundRendererParams
                    ) => {
                        return this.getRefundValueFormatted(
                            grid,
                            column,
                            params,
                            refundField
                        );
                    },
                } as CurrencyRefundRendererParams,
            };
        }

        if (commonHelpers.getValueOrDefault(column.data?.editable, false)) {
            colDef = {
                ...colDef,
                cellClass: SMART_GRID_CELL_CURRENCY_CLASS,
                cellRendererFramework: CurrencyDataCellComponent,
                cellRendererParams: {
                    getGrid: (params: CurrencyDataRendererParams) => {
                        return grid;
                    },
                    setCurrencyData: (
                        value: string,
                        params: CurrencyDataRendererParams
                    ) => {
                        const row: GridRow = params.data;
                        const xRow: GridRow = grid.body.rows.find(
                            x => x.id === row.id
                        );
                        grid.meta.api.saveData(value, xRow, column);
                    },
                } as CurrencyDataRendererParams,
            };
        }

        return colDef;
    }

    private getRefundField(column: GridColumn): string {
        const field = commonHelpers.getValueOrDefault(column.data?.field, '');
        return `${field}_refund`;
    }

    private getRefundValueFormatted(
        grid: Grid,
        column: GridColumn,
        params: ICellRendererParams,
        refundField: string
    ): string {
        const row: GridRow = params.data as GridRow;
        const refundStatsValue: GridRowDataStatsValue = commonHelpers.getValueOrDefault(
            row?.data?.stats[refundField],
            null
        ) as GridRowDataStatsValue;
        if (commonHelpers.isDefined(refundStatsValue?.value)) {
            const formatterOptions: FormatGridColumnValueOptions = {
                type: column.type,
                fractionSize: column.data?.fractionSize,
                currency: grid.meta.data.ext.currency,
                defaultValue: column.data?.defaultValue,
            };
            return formatGridColumnValue(
                refundStatsValue.value as string | number,
                formatterOptions
            );
        }
        return null;
    }
}
