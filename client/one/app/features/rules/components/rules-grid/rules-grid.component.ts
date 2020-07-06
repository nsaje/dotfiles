import './rules-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {Rule} from '../../../../core/rules/types/rule';
import {
    COLUMN_NAME,
    COLUMN_ACTION_TYPE,
    COLUMN_STATUS,
    COLUMN_ACTION_FREQUENCY,
    COLUMN_NOTIFICATION,
    COLUMN_SCOPE,
} from './rules-grid.component.config';

@Component({
    selector: 'zem-rules-grid',
    templateUrl: './rules-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RulesGridComponent implements OnChanges {
    @Input()
    rules: Rule[];
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    context: any;
    @Input()
    isLoading: boolean;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    columnDefs: ColDef[] = [
        COLUMN_NAME,
        COLUMN_ACTION_TYPE,
        COLUMN_STATUS,
        COLUMN_ACTION_FREQUENCY,
        COLUMN_NOTIFICATION,
        COLUMN_SCOPE,
    ];

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