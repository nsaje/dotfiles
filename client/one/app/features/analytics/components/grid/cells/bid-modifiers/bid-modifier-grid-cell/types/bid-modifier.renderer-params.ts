import {ICellRendererParams} from 'ag-grid-community';
import {BidModifier} from '../../../../../../../../core/bid-modifiers/types/bid-modifier';
import {GridBridgeComponent} from '../../../../grid-bridge/grid-bridge.component';
import {Grid} from '../../../../grid-bridge/types/grid';

export interface BidModifierRendererParams extends ICellRendererParams {
    context: {componentParent?: GridBridgeComponent};
    getGrid: (params: BidModifierRendererParams) => Grid;
    setBidModifier: (
        bidModifier: BidModifier,
        params: BidModifierRendererParams
    ) => void;
}
