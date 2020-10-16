import 'ag-grid-community/dist/styles/ag-grid.css';
import './smart-grid.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    OnInit,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {
    DetailGridInfo,
    GridApi,
    GridOptions,
    ColDef,
    RowSelectedEvent,
    SelectionChangedEvent,
    GridSizeChangedEvent,
} from 'ag-grid-community';
import {
    DEFAULT_GRID_OPTIONS,
    DEFAULT_PAGE_SIZE_OPTIONS,
} from './smart-grid.component.config';
import {GridLoadingOverlayComponent} from './components/overlays/grid-loading-overlay/grid-loading-overlay.component';
import {NoRowsOverlayComponent} from './components/overlays/no-rows-overlay/no-rows-overlay.component';
import * as commonHelpers from '../../helpers/common.helpers';
import * as arrayHelpers from '../../helpers/array.helpers';
import {PaginationOptions} from './types/pagination-options';
import {PageSizeConfig} from './types/page-size-config';
import {PaginationState} from './types/pagination-state';
import {HeaderCellComponent} from './components/cells/header-cell/header-cell.component';

@Component({
    selector: 'zem-smart-grid',
    templateUrl: './smart-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SmartGridComponent implements OnInit, OnChanges {
    @Input('gridOptions')
    options: GridOptions;
    @Input()
    columnDefs: ColDef[];
    @Input()
    rowData: any[];
    @Input()
    pinnedBottomRowData: any[];
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    paginationCount: number;
    @Input()
    context: any;
    @Output()
    rowSelected = new EventEmitter<any>();
    @Output()
    selectionChange = new EventEmitter<any[]>();
    @Output()
    gridReady = new EventEmitter<DetailGridInfo>();
    @Output()
    gridSizeChange = new EventEmitter<GridSizeChangedEvent>();
    @Output()
    paginationChange = new EventEmitter<PaginationState>();

    isGridReady: boolean;
    gridOptions: GridOptions;
    gridApi: GridApi;

    paginationPage: number;
    paginationPageSize: number;
    paginationPageSizeOptions: PageSizeConfig[];

    ngOnInit(): void {
        this.gridOptions = {
            ...DEFAULT_GRID_OPTIONS,
            ...commonHelpers.getValueOrDefault(this.options, {}),
            frameworkComponents: {
                loadingOverlayComponent: GridLoadingOverlayComponent,
                noRowsOverlayComponent: NoRowsOverlayComponent,
                agColumnHeader: HeaderCellComponent,
            },
        };
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (
            changes.paginationOptions &&
            commonHelpers.isDefined(this.paginationOptions)
        ) {
            this.paginationPage = commonHelpers.getValueOrDefault(
                this.paginationOptions.page,
                1
            );
            this.paginationPageSize = commonHelpers.getValueOrDefault(
                this.paginationOptions.pageSize,
                DEFAULT_PAGE_SIZE_OPTIONS[0].value
            );
            this.paginationPageSizeOptions = commonHelpers.getValueOrDefault(
                this.paginationOptions.pageSizeOptions,
                DEFAULT_PAGE_SIZE_OPTIONS
            );
        }
    }

    onRowSelected(event: RowSelectedEvent) {
        this.rowSelected.emit(event.data);
    }

    onSelectionChanged(event: SelectionChangedEvent) {
        this.selectionChange.emit(event.api.getSelectedRows());
    }

    onGridReady(params: DetailGridInfo) {
        this.isGridReady = true;
        this.gridApi = params.api;
        this.gridApi.sizeColumnsToFit();
        this.gridReady.emit(params);
    }

    onGridSizeChanged($event: GridSizeChangedEvent) {
        $event.api.sizeColumnsToFit();
        this.gridSizeChange.emit($event);
    }

    onPageChange(page: number) {
        this.paginationPage = page;
        switch (this.paginationOptions.type) {
            case 'client':
                this.gridApi.paginationGoToPage(page - 1);
                break;
            case 'server':
                this.gridApi.showLoadingOverlay();
                this.paginationChange.emit({
                    page: page,
                    pageSize: this.paginationPageSize,
                });
                break;
        }
    }

    onPaginationPageSizeChange(pageSize: number) {
        this.paginationPageSize = pageSize;
        switch (this.paginationOptions.type) {
            case 'client':
                this.gridApi.paginationSetPageSize(pageSize);
                break;
            case 'server':
                this.gridApi.showLoadingOverlay();
                this.paginationChange.emit({
                    page: this.paginationPage,
                    pageSize: pageSize,
                });
                break;
        }
    }

    canRenderPagination(): boolean {
        if (
            !this.isGridReady ||
            !commonHelpers.isDefined(this.paginationOptions)
        ) {
            return false;
        }

        switch (this.paginationOptions.type) {
            case 'client':
                return !arrayHelpers.isEmpty(this.rowData);
            case 'server':
                return (
                    commonHelpers.isDefined(this.paginationCount) &&
                    this.paginationCount > 0
                );
        }
    }

    getPaginationCount(): number {
        switch (this.paginationOptions.type) {
            case 'client':
                return this.rowData.length;
            case 'server':
                return this.paginationCount;
        }
    }
}
