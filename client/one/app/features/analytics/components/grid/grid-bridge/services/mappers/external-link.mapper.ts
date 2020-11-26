import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {ValueFormatterParams} from 'ag-grid-community';
import {LinkCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/link-cell/link-cell.component';
import {LinkRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/link-cell/types/link.renderer-params';
import {
    EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_COLUMN_WIDTH,
    EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_LINK_CELL_ICON,
} from '../../grid-bridge.component.config';
import {MIN_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridRow} from '../../types/grid-row';
import {GridRowDataStatsValue} from '../../types/grid-row-data';
import {ColumnMapper} from './column.mapper';

export class ExternalLinkColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): SmartGridColDef {
        return {
            minWidth: MIN_COLUMN_WIDTH,
            width: EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_COLUMN_WIDTH[column.type],
            cellRendererFramework: LinkCellComponent,
            cellRendererParams: {
                getText: (params: LinkRendererParams<GridRow>) => {
                    const value: GridRowDataStatsValue = params.value;
                    return value?.text;
                },
                getLink: (params: LinkRendererParams<GridRow>) => {
                    const value: GridRowDataStatsValue = params.value;
                    return value?.url;
                },
                getLinkIcon: (params: LinkRendererParams<GridRow>) => {
                    return EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_LINK_CELL_ICON[
                        column.type
                    ];
                },
            } as LinkRendererParams<GridRow>,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}
