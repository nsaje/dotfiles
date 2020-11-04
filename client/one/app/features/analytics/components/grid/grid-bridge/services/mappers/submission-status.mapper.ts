import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {SubmissionStatusCellComponent} from '../../../cells/submission-status-cell/submission-status-cell.component';
import {SUBMISSION_STATUS_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';

export class SubmissionStatusColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            colId: GridColumnTypes.SUBMISSION_STATUS,
            minWidth: SUBMISSION_STATUS_COLUMN_WIDTH,
            width: SUBMISSION_STATUS_COLUMN_WIDTH,
            cellRendererFramework: SubmissionStatusCellComponent,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}
