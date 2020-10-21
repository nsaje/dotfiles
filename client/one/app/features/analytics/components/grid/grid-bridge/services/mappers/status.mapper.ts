import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {BREAKDOWN_TO_STATUS_CONFIG} from '../../grid-bridge.component.config';
import {
    EntityStatus,
    STATUS_MIN_COLUMN_WIDTH,
} from '../../grid-bridge.component.constants';
import {GridRow} from '../../types/grid-row';

export class StatusColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            minWidth: STATUS_MIN_COLUMN_WIDTH,
            width: STATUS_MIN_COLUMN_WIDTH,
            valueFormatter: (params: ValueFormatterParams) => {
                const row: GridRow = params.data;
                if (commonHelpers.getValueOrDefault(row.data.archived, false)) {
                    return EntityStatus.ARCHIVED;
                }

                const statsValue: GridRowDataStatsValue = params.value;
                if (commonHelpers.isDefined(statsValue)) {
                    const config =
                        BREAKDOWN_TO_STATUS_CONFIG[grid.meta.data.breakdown];
                    if (commonHelpers.isDefined(config)) {
                        return config[statsValue.value] || '';
                    }
                }
                return '';
            },
        };
    }
}
