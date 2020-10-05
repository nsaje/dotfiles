import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';

export abstract class ColumnMapper {
    abstract map(grid: Grid, column: GridColumn): ColDef;
}
