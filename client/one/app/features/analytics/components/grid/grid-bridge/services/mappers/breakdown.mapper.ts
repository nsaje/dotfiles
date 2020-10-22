import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {BreakdownCellComponent} from '../../../cells/breakdown-cell/breakdown-cell.component';
import {BreakdownRendererParams} from '../../../cells/breakdown-cell/types/breakdown.renderer-params';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {
    BREAKDOWN_COLUMN_WIDTH,
    TOTALS_LABELS,
    TOTALS_LABEL_HELP_TEXT,
} from '../../grid-bridge.component.constants';
import {PinnedRowCellValueStyleClass} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component.constants';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';
import {GridRow} from '../../types/grid-row';
import {GridBridgeComponent} from '../../grid-bridge.component';

export class BreakdownColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            colId: GridColumnTypes.BREAKDOWN,
            minWidth: BREAKDOWN_COLUMN_WIDTH,
            width: BREAKDOWN_COLUMN_WIDTH,
            flex: 1,
            suppressSizeToFit: false,
            cellRendererFramework: BreakdownCellComponent,
            cellRendererParams: {
                getEntity: (params: BreakdownRendererParams) => {
                    const row: GridRow = params.data;
                    return row.entity;
                },
                getPopoverTooltip: (params: BreakdownRendererParams) => {
                    const statsValue: GridRowDataStatsValue = params.value;
                    return commonHelpers.getValueOrDefault(
                        statsValue?.popoverMessage,
                        ''
                    );
                },
                navigateByUrl: (
                    params: BreakdownRendererParams,
                    url: string
                ) => {
                    const component = params.context
                        .componentParent as GridBridgeComponent;
                    if (commonHelpers.isDefined(component)) {
                        component.navigateByUrl(url);
                    }
                },
            } as BreakdownRendererParams,
            pinnedRowCellRendererParams: {
                valueStyleClass: PinnedRowCellValueStyleClass.Strong,
                popoverTooltip: TOTALS_LABEL_HELP_TEXT,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return TOTALS_LABELS;
            },
        };
    }
}
