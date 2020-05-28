import './publisher-group-connections-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ColDef} from 'ag-grid-community';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {ConnectionActionsCellComponent} from '../../../../shared/components/connection-actions-cell/connection-actions-cell.component';
import {ConnectionRowParentComponent} from '../../../../shared/components/connection-actions-cell/types/connection-row-parent-component';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {PublisherGroupConnectionType} from '../../../../core/publisher-groups/types/publisher-group-connection-type';
import {CONNECTION_TYPE_NAMES} from '../../../../core/publisher-groups/types/publisher-group-connection.config';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';

@Component({
    selector: 'zem-publisher-group-connections-list',
    templateUrl: './publisher-group-connections-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublisherGroupConnectionsListComponent
    implements ConnectionRowParentComponent<PublisherGroupConnection> {
    @Input()
    connections: PublisherGroupConnection[];
    @Output()
    removeConnection = new EventEmitter<PublisherGroupConnection>();

    context: any;
    columnDefs: ColDef[] = [
        {headerName: 'Connection name', field: 'name'},
        {
            headerName: 'Connection type',
            field: 'location',
            valueFormatter: this.connectionLocationFormatter,
        },
        {
            headerName: '',
            width: 40,
            suppressSizeToFit: true,
            cellRendererFramework: ConnectionActionsCellComponent,
            pinned: 'right',
        },
    ];

    paginationOptions: PaginationOptions = {
        type: 'client',
        pageSizeOptions: [{name: '10', value: 10}],
        page: 1,
        pageSize: 10,
    };

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

    private connectionLocationFormatter(params: {
        value: PublisherGroupConnectionType;
    }): string {
        if (isDefined(params.value)) {
            return CONNECTION_TYPE_NAMES[params.value];
        }
        return 'N/A';
    }
}
