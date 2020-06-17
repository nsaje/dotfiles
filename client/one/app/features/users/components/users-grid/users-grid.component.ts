import './users-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import {User} from '../../../../core/users/types/user';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {
    COLUMN_ACCESS,
    COLUMN_EMAIL,
    COLUMN_NAME,
} from './users-grid.component.config';
import {UsersView} from '../../views/users.view';

@Component({
    selector: 'zem-users-grid',
    templateUrl: './users-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersGridComponent implements OnChanges {
    @Input()
    users: User[];
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    context: {componentParent: UsersView};
    @Input()
    isLoading: boolean;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    columnDefs: ColDef[] = [COLUMN_NAME, COLUMN_EMAIL, COLUMN_ACCESS];

    private gridApi: GridApi;

    ngOnChanges() {
        if (this.gridApi && this.isLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        if (this.isLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }
}
