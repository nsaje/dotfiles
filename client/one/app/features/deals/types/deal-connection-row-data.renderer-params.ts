import {ICellRendererParams} from 'ag-grid-community';
import {ConnectionsListComponent} from '../components/connections-list/connections-list.component';
import {DealConnectionRowData} from './deal-connection-row-data';

export interface DealConnectionRowDataRendererParams
    extends ICellRendererParams {
    context: {
        componentParent: ConnectionsListComponent;
    };
    data: DealConnectionRowData;
}
