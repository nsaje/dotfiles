import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {BreakdownCellComponent} from '../../../cells/breakdown-cell/breakdown-cell.component';
import {BreakdownRendererParams} from '../../../cells/breakdown-cell/types/breakdown.renderer-params';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';

export class BreakdownColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            cellRendererFramework: BreakdownCellComponent,
            cellRendererParams: {
                getPopoverTooltip: (params: BreakdownRendererParams) => {
                    const statsValue: GridRowDataStatsValue = params.value;
                    return commonHelpers.getValueOrDefault(
                        statsValue?.popoverMessage,
                        ''
                    );
                },
            } as BreakdownRendererParams,
        };
    }
}
