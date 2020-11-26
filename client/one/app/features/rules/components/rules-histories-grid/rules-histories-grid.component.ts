import './rules-histories-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {
    COLUMN_DATE_CREATE,
    COLUMN_RULE_NAME,
    COLUMN_AD_GROUP_NAME,
    COLUMN_CHANGES_FORMATTED,
    COLUMN_CHANGES_FORMATTED_TOOLTIP,
} from './rules-histories-grid.component.config';
import {RuleHistory} from '../../../../core/rules/types/rule-history';

@Component({
    selector: 'zem-rules-histories-grid',
    templateUrl: './rules-histories-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RulesHistoriesGridComponent implements OnChanges {
    @Input()
    rulesHistories: RuleHistory[];
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
        COLUMN_DATE_CREATE,
        COLUMN_RULE_NAME,
        COLUMN_AD_GROUP_NAME,
        COLUMN_CHANGES_FORMATTED,
        COLUMN_CHANGES_FORMATTED_TOOLTIP,
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
