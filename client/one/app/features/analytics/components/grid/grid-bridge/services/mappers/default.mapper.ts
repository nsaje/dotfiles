import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';

export class DefaultColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef | null {
        return null;
    }
}
