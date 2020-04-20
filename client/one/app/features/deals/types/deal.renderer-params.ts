import {ICellRendererParams} from 'ag-grid-community';
import {DealsView} from '../views/deals/deals.view';
import {Deal} from '../../../core/deals/types/deal';

export interface DealRendererParams extends ICellRendererParams {
    context: {
        componentParent: DealsView;
    };
    data: Deal;
}
