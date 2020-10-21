import {ColDef} from 'ag-grid-community';
import {getApproximateGridColumnWidth} from '../../helpers/grid-bridge.helpers';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';

export class StatsColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            width: getApproximateGridColumnWidth(column.data?.name),
        };
    }
}
