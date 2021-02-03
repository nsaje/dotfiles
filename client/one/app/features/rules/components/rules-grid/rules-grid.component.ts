import './rules-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
} from '@angular/core';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi, GridOptions} from 'ag-grid-community';
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
    COLUMN_RUNS_ON,
    COLUMN_ACTIONS,
    COLUMN_RUNS_ON_TOOLTIP,
} from './rules-grid.component.config';

@Component({
    selector: 'zem-rules-grid',
    templateUrl: './rules-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RulesGridComponent {
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

    columnDefs: SmartGridColDef[] = [
        COLUMN_STATUS,
        COLUMN_NAME,
        COLUMN_ACTION_TYPE,
        COLUMN_ACTION_FREQUENCY,
        COLUMN_NOTIFICATION,
        COLUMN_RUNS_ON,
        COLUMN_RUNS_ON_TOOLTIP,
        COLUMN_SCOPE,
        COLUMN_ACTIONS,
    ];

    gridOptions: GridOptions = {
        immutableData: true,
        getRowNodeId: this.getRowNodeId,
    };

    private gridApi: GridApi;

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }

    private getRowNodeId(rule: Rule): string {
        return rule.id;
    }
}
