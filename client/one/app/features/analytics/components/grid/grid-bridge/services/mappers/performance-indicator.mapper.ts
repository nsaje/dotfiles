import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {HeaderCellIcon} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {Emoticon} from '../../../../../../../app.constants';
import {PerformanceIndicatorCellComponent} from '../../../cells/performance-indicator-cell/performance-indicator-cell.component';
import {PERFORMANCE_INDICATOR_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {GridColumnTypes} from '../../../../../analytics.constants';

export class PerformanceIndicatorColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            colId: GridColumnTypes.PERFORMANCE_INDICATOR,
            minWidth: PERFORMANCE_INDICATOR_COLUMN_WIDTH,
            width: PERFORMANCE_INDICATOR_COLUMN_WIDTH,
            headerComponentParams: {
                icon: HeaderCellIcon.EmoticonHappy,
            } as HeaderParams,
            cellRendererFramework: PerformanceIndicatorCellComponent,
            valueFormatter: ((params: ValueFormatterParams) => {
                const statsValue: GridRowDataStatsValue = params.value;
                if (commonHelpers.isDefined(statsValue)) {
                    return commonHelpers.getValueOrDefault(
                        statsValue.overall,
                        Emoticon.NEUTRAL
                    );
                }
                return Emoticon.NEUTRAL;
            }) as any,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}
