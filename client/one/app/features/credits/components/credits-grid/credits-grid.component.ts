import './credits-grid.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {DetailGridInfo, GridApi, GridOptions} from 'ag-grid-community';
import {Credit} from '../../../../core/credits/types/credit';
import {CreditGridType} from '../../credits.constants';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {
    COLUMN_ID,
    COLUMN_CREATED_BY,
    COLUMN_VALID_FROM,
    COLUMN_VALID_TO,
    COLUMN_SIGNED,
    COLUMN_LICENSE_FEE,
    COLUMN_AMOUNT,
    COLUMN_ALLOCATED,
    COLUMN_AVAILABLE,
    COLUMN_SCOPE,
    COLUMN_NOTES,
    COLUMN_ACTION_CREDIT,
    COLUMN_ACTION_REFUND,
    COLUMN_CURRENCY,
    COLUMN_ACTION_REFUND_PAST,
    COLUMN_AMOUNT_PAST,
    COLUMN_SERVICE_FEE,
} from './credits-grid.component.config';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';

@Component({
    selector: 'zem-credits-grid',
    templateUrl: './credits-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditsGridComponent implements OnInit, OnChanges {
    @Input()
    credits: Credit[];
    @Input()
    creditGridType: CreditGridType;
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    context: any;
    @Input()
    isLoading: boolean;
    @Input()
    showLicenseFee: boolean;
    @Input()
    showServiceFee: boolean;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    paginationStateProperties = {
        [CreditGridType.ACTIVE]: {
            page: 'activePage',
            pageSize: 'activePageSize',
        },
        [CreditGridType.PAST]: {
            page: 'pastPage',
            pageSize: 'pastPageSize',
        },
    };

    gridOptions: GridOptions = {
        rowHeight: 40,
    };

    commonColumnDefs = {
        [CreditGridType.ACTIVE]: [
            COLUMN_ID,
            COLUMN_CREATED_BY,
            COLUMN_VALID_FROM,
            COLUMN_VALID_TO,
            COLUMN_SIGNED,
            COLUMN_CURRENCY,
            COLUMN_LICENSE_FEE,
            COLUMN_SERVICE_FEE,
            COLUMN_AMOUNT,
            COLUMN_ALLOCATED,
            COLUMN_AVAILABLE,
            COLUMN_SCOPE,
            COLUMN_NOTES,
            COLUMN_ACTION_CREDIT,
            COLUMN_ACTION_REFUND,
        ],
        [CreditGridType.PAST]: [
            COLUMN_ID,
            COLUMN_CREATED_BY,
            COLUMN_VALID_FROM,
            COLUMN_VALID_TO,
            COLUMN_SIGNED,
            COLUMN_CURRENCY,
            COLUMN_LICENSE_FEE,
            COLUMN_SERVICE_FEE,
            COLUMN_AMOUNT_PAST,
            COLUMN_ALLOCATED,
            COLUMN_AVAILABLE,
            COLUMN_SCOPE,
            COLUMN_NOTES,
            COLUMN_ACTION_REFUND_PAST,
        ],
    };

    columnDefs: SmartGridColDef[];

    private gridApi: GridApi;

    ngOnInit() {
        this.commonColumnDefs[this.creditGridType].find(
            column => column.field === 'licenseFee'
        ).hide = !this.showLicenseFee;
        this.commonColumnDefs[this.creditGridType].find(
            column => column.field === 'serviceFee'
        ).hide = !this.showServiceFee;
        this.columnDefs = this.commonColumnDefs[this.creditGridType];
    }

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

    onPaginationChange($event: PaginationState) {
        const paginationState = {
            [this.paginationStateProperties[this.creditGridType].page]:
                $event.page,
            [this.paginationStateProperties[this.creditGridType].pageSize]:
                $event.pageSize,
        } as any;
        this.paginationChange.emit(paginationState);
    }
}
