import './connection-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {ConnectionRowDataRendererParams} from './types/connection-row-data.renderer-params';

@Component({
    templateUrl: './connection-actions-cell.component.html',
})
export class ConnectionActionsCellComponent
    implements ICellRendererAngularComp {
    params: ConnectionRowDataRendererParams<any, any>;
    connection: any;
    isReadOnly: boolean = true;

    agInit(params: ConnectionRowDataRendererParams<any, any>) {
        this.params = params;
        this.connection = params.data;
        this.isReadOnly = params.context.componentParent.isConnectionReadonly(
            this.connection
        );
    }

    removeConnection() {
        this.params.context.componentParent.onRemoveConnection(this.connection);
    }

    refresh(): boolean {
        return false;
    }
}
