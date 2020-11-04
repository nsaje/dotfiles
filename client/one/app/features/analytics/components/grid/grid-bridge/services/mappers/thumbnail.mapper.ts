import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {ThumbnailCellComponent} from '../../../cells/thumbnail-cell/thumbnail-cell.component';
import {THUMBNAIL_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';

export class ThumbnailColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            colId: GridColumnTypes.THUMBNAIL,
            minWidth: THUMBNAIL_COLUMN_WIDTH,
            width: THUMBNAIL_COLUMN_WIDTH,
            cellRendererFramework: ThumbnailCellComponent,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}
