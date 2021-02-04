import './users-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    TemplateRef,
    ViewChild,
} from '@angular/core';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {User} from '../../../../core/users/types/user';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {
    COLUMN_ACCESS,
    COLUMN_ACTIONS,
    COLUMN_EMAIL,
    COLUMN_NAME,
    COLUMN_PERMISSIONS,
    COLUMN_REPORTS,
    COLUMN_STATUS,
} from './users-grid.component.config';
import {UsersView} from '../../views/users.view';

@Component({
    selector: 'zem-users-grid',
    templateUrl: './users-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersGridComponent {
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

    @ViewChild('accountAccessTemplate', {read: TemplateRef, static: false})
    accountAccessTemplate: TemplateRef<string[]>;

    columnDefs: SmartGridColDef[] = [
        COLUMN_NAME,
        COLUMN_EMAIL,
        COLUMN_STATUS,
        COLUMN_ACCESS,
        COLUMN_PERMISSIONS,
        COLUMN_REPORTS,
        COLUMN_ACTIONS,
    ];

    private gridApi: GridApi;

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;

        const columnAccessWithTemplate: SmartGridColDef = this.getColDefWithTemplate(
            COLUMN_ACCESS,
            this.accountAccessTemplate
        );
        $event.columnApi
            .getColumn(COLUMN_ACCESS.colId)
            .setColDef(columnAccessWithTemplate, null);
    }

    private getColDefWithTemplate(
        colDef: SmartGridColDef,
        template: TemplateRef<string[]>
    ): SmartGridColDef {
        return {
            ...COLUMN_ACCESS,
            cellRendererParams: {
                ...COLUMN_ACCESS.cellRendererParams,
                columnDisplayOptions: {
                    ...COLUMN_ACCESS.cellRendererParams.columnDisplayOptions,
                    iconTooltipTemplate: this.accountAccessTemplate,
                },
            },
        };
    }
}
