import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {CellClassParams} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import * as smartGridHelpers from '../../../../../../../shared/components/smart-grid/helpers/smart-grid.helpers';
import {
    MAX_COLUMN_WIDTH,
    MIN_COLUMN_WIDTH,
    SMART_GRID_CELL_METRIC_CLASS,
} from '../../grid-bridge.component.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {CellRole} from '../../../../../../../shared/components/smart-grid/smart-grid.component.constants';
import {METRIC_GRID_COLUMN_TYPES} from '../../grid-bridge.component.config';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';

export class StatsDataColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): SmartGridColDef {
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

        const cellRole = this.getCellRole(column);

        return {
            minWidth: MIN_COLUMN_WIDTH,
            width: columnWidth,
            headerComponentParams: {
                role: cellRole,
            } as HeaderParams,
            cellClassRules: {
                [SMART_GRID_CELL_METRIC_CLASS]: (params: CellClassParams) => {
                    return cellRole === CellRole.Metric;
                },
            },
            pinnedRowCellRendererParams: {
                valueStyleClass: null,
                popoverTooltip: null,
                popoverPlacement: 'top',
                role: cellRole,
            } as PinnedRowRendererParams,
        };
    }

    private getCellRole(column: GridColumn): CellRole {
        return METRIC_GRID_COLUMN_TYPES.includes(column.type)
            ? CellRole.Metric
            : CellRole.Dimension;
    }
}
