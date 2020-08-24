import './connections-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    Output,
    EventEmitter,
} from '@angular/core';
import {ColDef} from 'ag-grid-community';
import {ConnectionActionsCellComponent} from '../../../../shared/components/connection-actions-cell/connection-actions-cell.component';
import {DealConnectionRowData} from '../../types/deal-connection-row-data';
import {DealConnection} from 'one/app/core/deals/types/deal-connection';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {ConnectionRowParentComponent} from '../../../../shared/components/connection-actions-cell/types/connection-row-parent-component';

@Component({
    selector: 'zem-connections-list',
    templateUrl: './connections-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionsListComponent
    implements OnChanges, ConnectionRowParentComponent<DealConnectionRowData> {
    @Input()
    connections: DealConnection[];
    @Input()
    connectionType: 'account' | 'campaign' | 'adgroup';
    @Input()
    isReadOnly: boolean = true;
    @Output()
    removeConnection = new EventEmitter<string>();

    context: any;
    columnDefs: ColDef[] = [
        {headerName: 'Connection name', field: 'name'},
        {
            headerName: '',
            width: 40,
            suppressSizeToFit: true,
            cellRendererFramework: ConnectionActionsCellComponent,
            pinned: 'right',
        },
    ];
    rowData: DealConnectionRowData[];

    constructor() {
        this.context = {componentParent: this};
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.connections) {
            this.rowData = this.connections
                .filter((connection: DealConnection) => {
                    return commonHelpers.isNotEmpty(
                        connection[this.connectionType]
                    );
                })
                .map((connection: DealConnection) => {
                    return {
                        ...connection[this.connectionType],
                        connectionId: connection.id,
                        connectionType: this.connectionType,
                    };
                });
        }
    }

    onRemoveConnection(connection: DealConnectionRowData) {
        if (
            confirm(
                `Are you sure you wish to delete ${connection.name} connection?`
            )
        ) {
            this.removeConnection.emit(connection.connectionId);
        }
    }

    isConnectionReadonly(connection: DealConnectionRowData): boolean {
        return this.isReadOnly;
    }
}
