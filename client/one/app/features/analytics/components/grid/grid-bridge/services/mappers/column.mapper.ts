import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {PinnedRowCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component';
import {PinnedRowCellValueStyleClass} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component.constants';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {
    BREAKDOWN_MIN_COLUMN_WIDTH,
    MIN_COLUMN_WIDTH,
    NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN,
    NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
    TOTALS_LABELS,
    TOTALS_LABEL_HELP_TEXT,
} from '../../grid-bridge.component.constants';
import {
    getApproximateGridColumnWidth,
    formatGridColumnValue,
    FormatGridColumnValueOptions,
} from '../../helpers/grid-bridge.helper';
import {
    HeaderCellIcon,
    HeaderCellSort,
} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {
    PINNED_GRID_COLUMN_TYPES,
    RESIZABLE_GRID_COLUMN_TYPES,
} from '../../grid-bridge.component.config';
import {GridColumnOrder} from '../../types/grid-column-order';

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
        const defaultHeaderCellColDef = this.getDefaultHeaderCellColDef(
            grid,
            column
        );
        const defaultrowCellColDef = this.getDefaultRowCellColDef(grid, column);
        const defaultfooterCellColDef = this.getDefaultFooterCellColDef(
            grid,
            column
        );
        return {
            ...defaultHeaderCellColDef,
            ...defaultrowCellColDef,
            ...defaultfooterCellColDef,
        };
    }

    // tslint:disable-next-line: cyclomatic-complexity
    private getDefaultHeaderCellColDef(grid: Grid, column: GridColumn): ColDef {
        const approximateWidth: number = getApproximateGridColumnWidth(
            column.data?.name,
            column.type === GridColumnTypes.BREAKDOWN
                ? BREAKDOWN_MIN_COLUMN_WIDTH
                : MIN_COLUMN_WIDTH,
            NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
            NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
        );

        return {
            headerName: commonHelpers.getValueOrDefault(column.data?.name, ''),
            field: commonHelpers.getValueOrDefault(column.data?.field, ''),
            colId: commonHelpers.getValueOrDefault(column.data?.field, ''),
            sortable: commonHelpers.getValueOrDefault(
                column.data?.order,
                false
            ),
            sort: commonHelpers.getValueOrDefault(
                column.order,
                GridColumnOrder.NONE
            ),
            minWidth:
                column.type === GridColumnTypes.BREAKDOWN
                    ? BREAKDOWN_MIN_COLUMN_WIDTH
                    : MIN_COLUMN_WIDTH,
            width: approximateWidth,
            flex: column.type === GridColumnTypes.BREAKDOWN ? 1 : 0,
            suppressSizeToFit: column.type !== GridColumnTypes.BREAKDOWN,
            resizable: RESIZABLE_GRID_COLUMN_TYPES.includes(column.type),
            pinned: PINNED_GRID_COLUMN_TYPES.includes(column.type)
                ? 'left'
                : null,
            headerComponentParams: {
                icon:
                    column.type === GridColumnTypes.PERFORMANCE_INDICATOR
                        ? HeaderCellIcon.EmoticonHappy
                        : null,
                internalFeature: commonHelpers.getValueOrDefault(
                    column.data?.internal,
                    false
                ),
                sortOptions: {
                    sortType: 'server',
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
        };
    }

    private getDefaultRowCellColDef(grid: Grid, column: GridColumn): ColDef {
        return {
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
        };
    }

    private getDefaultFooterCellColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            pinnedRowCellRendererFramework: PinnedRowCellComponent,
            pinnedRowCellRendererParams: {
                valueStyleClass:
                    column.type === GridColumnTypes.BREAKDOWN
                        ? PinnedRowCellValueStyleClass.Strong
                        : null,
                popoverTooltip:
                    column.type === GridColumnTypes.BREAKDOWN
                        ? TOTALS_LABEL_HELP_TEXT
                        : null,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                const statsValue: GridRowDataStatsValue = params.value;
                if (column.type === GridColumnTypes.BREAKDOWN) {
                    return TOTALS_LABELS;
                }
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
