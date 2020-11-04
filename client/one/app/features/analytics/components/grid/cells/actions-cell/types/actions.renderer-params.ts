import {ICellRendererParams} from 'ag-grid-community';
import {GridBridgeComponent} from '../../../grid-bridge/grid-bridge.component';
import {Grid} from '../../../grid-bridge/types/grid';
import {GridRow} from '../../../grid-bridge/types/grid-row';
import {BreakdownRendererParams} from '../../breakdown-cell/types/breakdown.renderer-params';

export interface ActionsRendererParams extends ICellRendererParams {
    context: {componentParent?: GridBridgeComponent};
    getGrid: (params: BreakdownRendererParams) => Grid;
    getGridRow: (params: BreakdownRendererParams) => GridRow;
}
