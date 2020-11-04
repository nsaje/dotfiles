import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {BidModifierGridCellComponent} from '../../../cells/bid-modifiers/bid-modifier-grid-cell/bid-modifier-grid-cell.component';
import {BidModifierRendererParams} from '../../../cells/bid-modifiers/bid-modifier-grid-cell/type/bid-modifier.renderer-params';
import {
    BID_MODIFIER_COLUMN_WIDTH,
    SMART_GRID_CELL_BID_MODIFIER_CLASS,
} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridRow} from '../../types/grid-row';
import {GridRowDataStats} from '../../types/grid-row-data';
import {ColumnMapper} from './column.mapper';

export class BidModifierColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return {
            colId: GridColumnTypes.BID_MODIFIER_FIELD,
            minWidth: BID_MODIFIER_COLUMN_WIDTH,
            width: BID_MODIFIER_COLUMN_WIDTH,
            cellRendererFramework: BidModifierGridCellComponent,
            cellRendererParams: {
                getGrid: (params: BidModifierRendererParams) => {
                    return grid;
                },
                setBidModifier: (
                    bidModifier: BidModifier,
                    params: BidModifierRendererParams
                ) => {
                    const row: GridRow = params.data;
                    const stats: GridRowDataStats = {
                        ...row.data.stats,
                        bid_modifier: {
                            ...row.data.stats.bid_modifier,
                            value: {
                                ...(row.data.stats.bid_modifier
                                    .value as BidModifier),
                                modifier: bidModifier.modifier,
                            } as BidModifier,
                        },
                    };
                    grid.meta.api.updateRowStats(row.data.breakdownId, stats);
                    const rowNode = params.api.getRowNode(row.id);
                    params.api.flashCells({
                        columns: [GridColumnTypes.BID_MODIFIER_FIELD],
                        rowNodes: [rowNode],
                    });
                },
            } as BidModifierRendererParams,
            cellClass: SMART_GRID_CELL_BID_MODIFIER_CLASS,
            valueFormatter: (params: ValueFormatterParams) => {
                return params.value;
            },
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}
