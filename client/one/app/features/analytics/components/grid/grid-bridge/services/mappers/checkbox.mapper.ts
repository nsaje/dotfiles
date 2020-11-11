import {ColDef} from 'ag-grid-community';
import {CheckboxCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {
    GridColumnTypes,
    GridSelectionFilterType,
} from '../../../../../analytics.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {CheckboxRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/types/checkbox.renderer-params';
import {GridRow} from '../../types/grid-row';
import {
    CHECKBOX_COLUMN_WIDTH,
    CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
} from '../../grid-bridge.component.constants';
import {CheckboxFilterHeaderCellComponent} from '../../../cells/checkbox-filter-header-cell/checkbox-filter-header-cell.component';
import {CheckboxFilterHeaderParams} from '../../../cells/checkbox-filter-header-cell/types/checkbox-filter-header-params';
import {GridSelectionCustomFilter} from '../../types/grid-selection-custom-filter';
import {HEADER_CHECKBOX_WITH_FILTERS_BREAKDOWNS} from '../../grid-bridge.component.config';

export class CheckboxColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef | null {
        let colDef: ColDef = {
            field: GridColumnTypes.CHECKBOX,
            colId: GridColumnTypes.CHECKBOX,
            minWidth: CHECKBOX_COLUMN_WIDTH,
            width: CHECKBOX_COLUMN_WIDTH,
            headerComponentParams: {
                enableSelection: true,
                selectionOptions: {
                    isChecked: (params: HeaderParams) => {
                        const selection: any = grid.meta.api.getSelection();
                        if (commonHelpers.isDefined(selection)) {
                            return (
                                selection.type === GridSelectionFilterType.ALL
                            );
                        }
                        return false;
                    },
                    isDisabled: (params: HeaderParams) => {
                        return false;
                    },
                    setChecked: (value: boolean, params: HeaderParams) => {
                        if (!value) {
                            grid.meta.api.setSelectionFilter(
                                GridSelectionFilterType.NONE
                            );
                        } else {
                            grid.meta.api.setSelectionFilter(
                                GridSelectionFilterType.ALL
                            );
                        }
                    },
                },
            } as HeaderParams,
            cellRendererFramework: CheckboxCellComponent,
            cellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {
                    const row: GridRow = params.data;
                    const xRow = grid.body.rows.find(x => x.id === row.id);
                    if (commonHelpers.isDefined(xRow)) {
                        return grid.meta.api.isRowSelected(xRow);
                    }
                    return false;
                },
                isDisabled: (params: CheckboxRendererParams) => {
                    const row: GridRow = params.data;
                    const xRow = grid.body.rows.find(x => x.id === row.id);
                    if (commonHelpers.isDefined(xRow)) {
                        return !grid.meta.api.isRowSelectable(xRow);
                    }
                    return true;
                },
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {
                    const row: GridRow = params.data;
                    const xRow = grid.body.rows.find(x => x.id === row.id);
                    if (commonHelpers.isDefined(xRow)) {
                        grid.meta.api.setRowSelection(xRow, value);
                    }
                },
            } as CheckboxRendererParams,
            valueFormatter: '',
            valueGetter: '',
            pinnedRowCellRendererFramework: CheckboxCellComponent,
            pinnedRowCellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {
                    return grid.meta.api.isRowSelected(grid.footer.row);
                },
                isDisabled: (params: CheckboxRendererParams) => {
                    return !grid.meta.api.isRowSelectable(grid.footer.row);
                },
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {
                    grid.meta.api.setRowSelection(grid.footer.row, value);
                },
            } as CheckboxRendererParams,
            pinnedRowValueFormatter: '',
        };

        if (
            HEADER_CHECKBOX_WITH_FILTERS_BREAKDOWNS.includes(
                grid.meta.data.breakdown
            )
        ) {
            colDef = {
                ...colDef,
                minWidth: CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
                width: CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
                headerComponentFramework: CheckboxFilterHeaderCellComponent,
                headerComponentParams: {
                    isChecked: (params: CheckboxFilterHeaderParams) => {
                        const selection: any = grid.meta.api.getSelection();
                        if (commonHelpers.isDefined(selection)) {
                            return (
                                selection.type === GridSelectionFilterType.ALL
                            );
                        }
                        return false;
                    },
                    setChecked: (
                        value: boolean,
                        params: CheckboxFilterHeaderParams
                    ) => {
                        if (!value) {
                            grid.meta.api.setSelectionFilter(
                                GridSelectionFilterType.NONE
                            );
                        } else {
                            grid.meta.api.setSelectionFilter(
                                GridSelectionFilterType.ALL
                            );
                        }
                    },
                    getCustomFilters: (params: CheckboxFilterHeaderParams) => {
                        return grid.meta.api.getCustomFilters();
                    },
                    setCustomFilter: (
                        value: GridSelectionCustomFilter,
                        params: CheckboxFilterHeaderParams
                    ) => {
                        grid.meta.api.setSelectionFilter(
                            GridSelectionFilterType.CUSTOM,
                            value
                        );
                    },
                } as CheckboxFilterHeaderParams,
            };
        }

        return colDef;
    }
}
