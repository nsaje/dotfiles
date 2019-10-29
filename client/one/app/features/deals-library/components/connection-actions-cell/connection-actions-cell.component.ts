import './connection-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {DealConnectionEntity} from '../../../../core/deals/types/deal-connection-entity';

@Component({
    templateUrl: './connection-actions-cell.component.html',
})
export class ConnectionActionsCellComponent
    implements ICellRendererAngularComp {
    connection: DealConnectionEntity;
    params: any;

    agInit(params: any) {
        this.params = params;
        this.connection = params.data;
    }

    removeConnection() {
        this.params.context.componentParent.removeConnection(this.connection);
    }

    refresh(): boolean {
        return false;
    }
}
