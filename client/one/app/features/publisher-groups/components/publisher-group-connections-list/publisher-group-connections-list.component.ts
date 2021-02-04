import './publisher-group-connections-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {ConnectionRowParentComponent} from '../../../../shared/components/connection-actions-cell/types/connection-row-parent-component';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {
    COLUMN_ACTIONS,
    COLUMN_USED_AS,
    COLUMN_USED_ON,
    PAGINATION_OPTIONS,
} from './publisher-groups-connections-list.component.config';

@Component({
    selector: 'zem-publisher-group-connections-list',
    templateUrl: './publisher-group-connections-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublisherGroupConnectionsListComponent
    implements ConnectionRowParentComponent<PublisherGroupConnection> {
    @Input()
    connections: PublisherGroupConnection[];
    @Input()
    isLoading: boolean = false;
    @Input()
    isReadOnly: boolean = true;
    @Output()
    removeConnection = new EventEmitter<PublisherGroupConnection>();

    context: any;
    columnDefs: SmartGridColDef[] = [
        COLUMN_USED_ON,
        COLUMN_USED_AS,
        COLUMN_ACTIONS,
    ];

    paginationOptions: PaginationOptions = PAGINATION_OPTIONS;
    private gridApi: GridApi;

    constructor() {
        this.context = {componentParent: this};
    }

    onRemoveConnection(connection: PublisherGroupConnection) {
        if (
            confirm(
                `Are you sure you wish to delete ${connection.name} connection?`
            )
        ) {
            this.removeConnection.emit(connection);
        }
    }

    isConnectionReadonly(connection: PublisherGroupConnection): boolean {
        return this.isReadOnly;
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }
}
