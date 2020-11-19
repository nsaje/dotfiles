import './deals-grid.component.less';
import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
} from '@angular/core';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {
    COLUMN_ACCOUNTS,
    COLUMN_ACTIONS,
    COLUMN_AD_GROUPS,
    COLUMN_CAMPAIGNS,
    COLUMN_CREATED_BY,
    COLUMN_DEAL_ID,
    COLUMN_DEAL_NAME,
    COLUMN_FLOOR_PRICE,
    COLUMN_ID,
    COLUMN_NOTES,
    COLUMN_SCOPE,
    COLUMN_SOURCE,
    COLUMN_VALID_FROM,
    COLUMN_VALID_TO,
} from './deals-grid.component.config';
import {DealsView} from '../../views/deals/deals.view';
import {FormattedDeal} from '../../types/formatted-deal';

@Component({
    selector: 'zem-deals-grid',
    templateUrl: './deals-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealsGridComponent implements OnChanges {
    @Input()
    deals: FormattedDeal[];
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    context: {componentParent: DealsView};
    @Input()
    isLoading: boolean;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    columnDefs: ColDef[] = [
        COLUMN_ID,
        COLUMN_DEAL_NAME,
        COLUMN_DEAL_ID,
        COLUMN_SOURCE,
        COLUMN_FLOOR_PRICE,
        COLUMN_VALID_FROM,
        COLUMN_VALID_TO,
        COLUMN_SCOPE,
        COLUMN_ACCOUNTS,
        COLUMN_CAMPAIGNS,
        COLUMN_AD_GROUPS,
        COLUMN_NOTES,
        COLUMN_CREATED_BY,
        COLUMN_ACTIONS,
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