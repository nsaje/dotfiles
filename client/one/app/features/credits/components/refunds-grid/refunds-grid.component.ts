import './refunds-grid.component.less';

import {
    Input,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    OnInit,
} from '@angular/core';
import {ColDef, DetailGridInfo, GridApi, GridOptions} from 'ag-grid-community';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {CreditRefund} from '../../../../core/credits/types/credit-refund';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {Credit} from '../../../../core/credits/types/credit';
import {NoteCellComponent} from '../../../../shared/components/smart-grid/components/cell/note-cell/note-cell.component';
import {NoteRendererParams} from '../../../../shared/components/smart-grid/components/cell/note-cell/types/note.renderer-params';

@Component({
    selector: 'zem-refunds-grid',
    templateUrl: './refunds-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RefundsGridComponent implements OnInit {
    @Input()
    refunds: CreditRefund[];
    @Input()
    credit: Credit;
    @Input()
    context: any;
    @Input()
    isLoading: boolean;
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    formattedCreditTotal: string;

    gridOptions: GridOptions = {
        rowHeight: 40,
    };

    columnDefs: ColDef[] = [
        {
            headerName: 'ID',
            field: 'id',
            width: 80,
            minWidth: 80,
            resizable: false,
        },
        {
            headerName: 'Created By',
            width: 140,
            minWidth: 140,
            cellRendererFramework: NoteCellComponent,
            cellRendererParams: {
                getMainContent: item => item.createdBy,
                getNote: item =>
                    dateTimeFormatter('MM/DD/YYYY')({value: item.createdDt}),
            } as NoteRendererParams<CreditRefund>,
        },
        {
            headerName: 'Valid from',
            field: 'startDate',
            width: 100,
            minWidth: 100,
            resizable: false,
            valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
        },
        {
            headerName: 'Valid to',
            field: 'endDate',
            width: 100,
            minWidth: 100,
            resizable: false,
            valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
        },
        {
            headerName: 'Refund Amount',
            field: 'amount',
            width: 100,
            minWidth: 100,
            resizable: false,
            valueFormatter: params => {
                return getValueInCurrency(params.value, this.credit.currency);
            },
        },
        {
            headerName: 'Notes',
            field: 'comment',
            maxWidth: 50,
            minWidth: 50,
            resizable: false,
            cellRendererFramework: IconTooltipCellComponent,
            cellRendererParams: {
                icon: IconTooltipCellIcon.Comment,
            } as IconTooltipRendererParams,
        },
    ];

    private gridApi: GridApi;

    ngOnInit() {
        this.formattedCreditTotal = getValueInCurrency(
            this.credit.total,
            this.credit.currency
        );
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        if (this.isLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }
}