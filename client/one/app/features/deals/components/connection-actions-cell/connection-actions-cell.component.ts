import './connection-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {DealConnectionRowDataRendererParams} from '../../types/deal-connection-row-data.renderer-params';
import {DealConnectionRowData} from '../../types/deal-connection-row-data';

@Component({
    templateUrl: './connection-actions-cell.component.html',
})
export class ConnectionActionsCellComponent
    implements ICellRendererAngularComp {
    params: DealConnectionRowDataRendererParams;
    connection: DealConnectionRowData;

    agInit(params: DealConnectionRowDataRendererParams) {
        this.params = params;
        this.connection = params.data;
    }

    removeConnection() {
        this.params.context.componentParent.onRemoveConnection(this.connection);
    }

    refresh(): boolean {
        return false;
    }
}
