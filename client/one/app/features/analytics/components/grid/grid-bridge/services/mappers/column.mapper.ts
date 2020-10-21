import {
    ColDef,
    ValueFormatterParams,
    ValueGetterParams,
} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {PinnedRowCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';
import {MIN_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {
    formatGridColumnValue,
    FormatGridColumnValueOptions,
} from '../../helpers/grid-bridge.helpers';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {
    PINNED_GRID_COLUMN_TYPES,
    RESIZABLE_GRID_COLUMN_TYPES,
} from '../../grid-bridge.component.config';
import {GridColumnOrder} from '../../types/grid-column-order';
import {GridRow} from '../../types/grid-row';

export abstract class ColumnMapper {
    map(grid: Grid, column: GridColumn): ColDef {
        const defaultColDef = this.getDefaultColDef(grid, column);
        const colDef = this.getColDef(grid, column);
        return {...defaultColDef, ...(colDef || {})};
    }

    abstract getColDef(grid: Grid, column: GridColumn): ColDef;

    //
    // PRIVATE METHODS
    //

    private getDefaultColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            headerName: commonHelpers.getValueOrDefault(column.data?.name, ''),
            field: commonHelpers.getValueOrDefault(column.data?.field, ''),
            colId: commonHelpers.getValueOrDefault(column.data?.field, ''),
            minWidth: MIN_COLUMN_WIDTH,
            width: MIN_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: RESIZABLE_GRID_COLUMN_TYPES.includes(column.type),
            pinned: PINNED_GRID_COLUMN_TYPES.includes(column.type)
                ? 'left'
                : null,
            headerComponentParams: {
                icon: null,
                internalFeature: commonHelpers.getValueOrDefault(
                    column.data?.internal,
                    false
                ),
                enableSorting: commonHelpers.getValueOrDefault(
                    column.data?.order,
                    false
                ),
                sortOptions: {
                    sortType: 'server',
                    sort: (commonHelpers.getValueOrDefault(
                        column.order,
                        GridColumnOrder.NONE
                    ) as any) as HeaderCellSort,
                    orderField: commonHelpers.getValueOrDefault(
                        column.data?.orderField,
                        null
                    ),
                    initialSort: commonHelpers.getValueOrDefault(
                        (column.data?.initialOrder as any) as HeaderCellSort,
                        null
                    ),
                    setSortModel: (sortModel: SortModel[]) => {
                        sortModel.forEach(model => {
                            grid.meta.orderService.setColumnOrder(
                                column,
                                model.sort
                            );
                        });
                    },
                },
                popoverTooltip: commonHelpers.getValueOrDefault(
                    column.data?.help,
                    null
                ),
                popoverPlacement: 'top',
            } as HeaderParams,
            valueFormatter: (params: ValueFormatterParams) => {
                const statsValue: GridRowDataStatsValue = params.value;
                if (commonHelpers.isDefined(statsValue)) {
                    const formatterOptions: FormatGridColumnValueOptions = {
                        type: column.type,
                        fractionSize: column.data?.fractionSize,
                        currency: grid.meta.data.ext.currency,
                        defaultValue: column.data?.defaultValue,
                    };
                    return formatGridColumnValue(
                        statsValue.value,
                        formatterOptions
                    );
                }
                return '';
            },
            valueGetter: (params: ValueGetterParams) => {
                const row: GridRow = params.data;
                const field = params.column.getColDef().field;
                return row.data.stats[field];
            },
            pinnedRowCellRendererFramework: PinnedRowCellComponent,
            pinnedRowCellRendererParams: {
                valueStyleClass: null,
                popoverTooltip: null,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                const statsValue: GridRowDataStatsValue = params.value;
                if (commonHelpers.isDefined(statsValue)) {
                    const formatterOptions: FormatGridColumnValueOptions = {
                        type: column.type,
                        fractionSize: column.data?.fractionSize,
                        currency: grid.meta.data.ext.currency,
                        defaultValue: column.data?.defaultValue,
                    };
                    return formatGridColumnValue(
                        statsValue.value,
                        formatterOptions
                    );
                }
                return '';
            },
        };
    }
}
