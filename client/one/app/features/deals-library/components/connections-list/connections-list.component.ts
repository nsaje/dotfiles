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
import {PaginationOptions} from 'one/app/shared/components/smart-grid/types/pagination-options';
import {ColDef} from 'ag-grid-community';
import {ConnectionActionsCellComponent} from '../connection-actions-cell/connection-actions-cell.component';
import {DealConnectionRowData} from '../../types/deal-connection-row-data';
import {DealConnection} from 'one/app/core/deals/types/deal-connection';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-connections-list',
    templateUrl: './connections-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionsListComponent implements OnChanges {
    @Input()
    connections: DealConnection[];
    @Input()
    connectionType: 'account' | 'campaign' | 'adgroup';
    @Output()
    removeConnection = new EventEmitter<string>();

    context: any;
    paginationOptions: PaginationOptions = {
        type: 'client',
    };
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
}
