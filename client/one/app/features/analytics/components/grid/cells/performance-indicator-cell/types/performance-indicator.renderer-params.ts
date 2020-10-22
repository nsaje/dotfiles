import {ICellRendererParams} from 'ag-grid-community';
import {GridBridgeComponent} from '../../../grid-bridge/grid-bridge.component';

export interface PerformanceIndicatorRendererParams
    extends ICellRendererParams {
    context: {componentParent?: GridBridgeComponent};
}
