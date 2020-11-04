import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {SMART_GRID_CELL_CURRENCY_CLASS} from '../../grid-bridge.component.constants';
import {CurrencyDataRendererParams} from '../../../cells/currency-data-cell/type/currency-data.renderer-params';
import {GridRow} from '../../types/grid-row';
import {CurrencyDataCellComponent} from '../../../cells/currency-data-cell/currency-data-cell.component';
import {StatsDataColumnMapper} from './stats-data.mapper';

export class CurrencyDataColumnMapper extends StatsDataColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        let colDef: ColDef = super.getColDef(grid, column);
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
}
