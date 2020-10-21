import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {ACTIONS_MIN_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {GridRow} from '../../types/grid-row';
import {ActionsCellComponent} from '../../../cells/actions-cell/actions-cell.component';
import {ActionsRendererParams} from '../../../cells/actions-cell/types/actions.renderer-params';
import {GridColumnTypes} from '../../../../../analytics.constants';

export class ActionsColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            field: GridColumnTypes.ACTIONS,
            colId: GridColumnTypes.ACTIONS,
            minWidth: ACTIONS_MIN_COLUMN_WIDTH,
            width: ACTIONS_MIN_COLUMN_WIDTH,
            cellRendererFramework: ActionsCellComponent,
            cellRendererParams: {
                getGrid: (params: ActionsRendererParams) => {
                    return grid;
                },
                getGridRow: (params: ActionsRendererParams) => {
                    const row: GridRow = params.data;
                    const xRow = grid.body.rows.find(x => x.id === row.id);
                    return commonHelpers.getValueOrDefault(xRow, null);
                },
            } as ActionsRendererParams,
            valueFormatter: '',
            valueGetter: '',
            pinnedRowValueFormatter: '',
        };
    }
}
