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
import {GridRowDataStats} from '../../types/grid-row-data';
import {GridRow} from '../../types/grid-row';

export class CheckboxColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef | null {
        const headerCellColDef = this.getHeaderCellColDef(grid, column);
        const rowCellColDef = this.getRowCellColDef(grid, column);
        const footerCellColDef = this.getFooterCellColDef(grid, column);
        return {...headerCellColDef, ...rowCellColDef, ...footerCellColDef};
    }

    private getHeaderCellColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            headerName: '',
            field: GridColumnTypes.CHECKBOX,
            colId: GridColumnTypes.CHECKBOX,
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
        };
    }

    private getRowCellColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            cellRendererFramework: CheckboxCellComponent,
            cellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {
                    const statsRow: GridRowDataStats = params.data;
                    if (
                        commonHelpers.isDefined(statsRow) &&
                        commonHelpers.isDefined(statsRow.id)
                    ) {
                        const row: GridRow = grid.body.rows.find(
                            row => row.id === statsRow.id.value
                        );
                        if (commonHelpers.isDefined(row)) {
                            return grid.meta.api.isRowSelected(row);
                        }
                    }
                    return false;
                },
                isDisabled: (params: CheckboxRendererParams) => {
                    const statsRow: GridRowDataStats = params.data;
                    if (
                        commonHelpers.isDefined(statsRow) &&
                        commonHelpers.isDefined(statsRow.id)
                    ) {
                        const row: GridRow = grid.body.rows.find(
                            row => row.id === statsRow.id.value
                        );
                        if (commonHelpers.isDefined(row)) {
                            return !grid.meta.api.isRowSelectable(row);
                        }
                    }
                    return true;
                },
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {
                    const statsRow: GridRowDataStats = params.data;
                    const row = grid.body.rows.find(
                        row => row.id === statsRow.id.value
                    );
                    grid.meta.api.setRowSelection(row, value);
                },
            } as CheckboxRendererParams,
            valueFormatter: '',
            valueGetter: '',
        };
    }

    private getFooterCellColDef(grid: Grid, column: GridColumn): ColDef {
        return {
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
        };
    }
}
