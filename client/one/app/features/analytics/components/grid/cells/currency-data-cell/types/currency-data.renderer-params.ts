import {ICellRendererParams} from 'ag-grid-community';
import {GridBridgeComponent} from '../../../grid-bridge/grid-bridge.component';
import {Grid} from '../../../grid-bridge/types/grid';

export interface CurrencyDataRendererParams extends ICellRendererParams {
    context: {componentParent?: GridBridgeComponent};
    getGrid: (params: CurrencyDataRendererParams) => Grid;
    setCurrencyData: (
        value: string,
        params: CurrencyDataRendererParams
    ) => void;
}
