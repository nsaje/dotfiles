import {ICellRendererParams} from 'ag-grid-community';
import {Placement} from '../../../../../../../shared/types/placement';
import {GridBridgeComponent} from '../../../grid-bridge/grid-bridge.component';
import {GridRowEntity} from '../../../grid-bridge/types/grid-row-entity';

export interface BreakdownRendererParams extends ICellRendererParams {
    context: {componentParent?: GridBridgeComponent};
    getEntity?: (params: BreakdownRendererParams) => GridRowEntity;
    getPopoverTooltip?: (params: BreakdownRendererParams) => string;
    popoverPlacement?: Placement;
    navigateByUrl?: (params: BreakdownRendererParams, url: string) => void;
}
