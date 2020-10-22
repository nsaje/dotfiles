import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import * as smartGridHelpers from '../../../../../../../shared/components/smart-grid/helpers/smart-grid.helpers';
import {
    MAX_COLUMN_WIDTH,
    MIN_COLUMN_WIDTH,
} from '../../grid-bridge.component.constants';

export class StatsColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        const headerName: string = commonHelpers.getValueOrDefault(
            column.data?.name,
            ''
        );
        const includeCheckboxWidth = false;
        const includeHelpPopoverWidth = commonHelpers.isDefined(
            column.data?.help
        );
        const includeSortArrowWidth = commonHelpers.getValueOrDefault(
            column.data?.order,
            false
        );

        const columnWidth = smartGridHelpers.getApproximateColumnWidth(
            headerName,
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            includeCheckboxWidth,
            includeHelpPopoverWidth,
            includeSortArrowWidth
        );

        return {
            minWidth: columnWidth,
            width: columnWidth,
        };
    }
}
