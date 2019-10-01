import 'ag-grid-community/dist/styles/ag-grid.css';
import './smart-grid.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    OnInit,
    OnDestroy,
    Renderer2,
} from '@angular/core';
import {DetailGridInfo, GridApi, GridOptions, ColDef} from 'ag-grid-community';
import {
    DEFAULT_GRID_OPTIONS,
    DEFAULT_PAGE_SIZE_OPTIONS,
} from './smart-grid.component.config';
import {LoadingOverlayComponent} from './components/loading-overlay/loading-overlay.component';
import {NoRowsOverlayComponent} from './components/no-rows-overlay/no-rows-overlay.component';
import * as commonHelpers from '../../helpers/common.helpers';
import {PaginationOptions} from './types/pagination-options';
import {PageSizeConfig} from './types/page-size-config';

@Component({
    selector: 'zem-smart-grid',
    templateUrl: './smart-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SmartGridComponent implements OnInit, OnDestroy {
    @Input('gridOptions')
    options: GridOptions;
    @Input()
    columnDefs: ColDef[];
    @Input()
    rowData: any[];
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    paginationCount: number;
    @Output()
    gridReady = new EventEmitter<DetailGridInfo>();
    @Output()
    pageChange = new EventEmitter<number>();
    @Output()
    pageSizeChange = new EventEmitter<number>();

    isGridReady: boolean;
    gridOptions: GridOptions;
    gridApi: GridApi;

    paginationPage: number;
    paginationPageSize: number;
    paginationPageSizeOptions: PageSizeConfig[];

    private windowResizeListener: Function;

    constructor(private renderer: Renderer2) {}

    ngOnInit(): void {
        this.gridOptions = {
            ...DEFAULT_GRID_OPTIONS,
            ...commonHelpers.getValueOrDefault(this.options, {}),
            frameworkComponents: {
                loadingOverlayComponent: LoadingOverlayComponent,
                noRowsOverlayComponent: NoRowsOverlayComponent,
            },
        };
        if (commonHelpers.isDefined(this.paginationOptions)) {
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
        this.windowResizeListener = this.renderer.listen(
            window,
            'resize',
            () => {
                if (this.isGridReady) {
                    this.gridApi.sizeColumnsToFit();
                }
            }
        );
    }

    ngOnDestroy(): void {
        this.removeEventListener(this.windowResizeListener);
    }

    onGridReady(params: DetailGridInfo) {
        this.isGridReady = true;
        this.gridApi = params.api;
        this.gridApi.sizeColumnsToFit();
        this.gridReady.emit(params);
    }

    onRowDataChanged(params: DetailGridInfo) {
        if (this.isGridReady) {
            this.gridApi.hideOverlay();
        }
    }

    onPageChange(page: number) {
        this.paginationPage = page;
        switch (this.paginationOptions.type) {
            case 'client':
                this.gridApi.paginationGoToPage(page - 1);
                break;
            case 'server':
                this.gridApi.showLoadingOverlay();
                this.pageChange.emit(page);
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
                this.pageSizeChange.emit(pageSize);
                break;
        }
    }

    private removeEventListener(eventListener: Function): void {
        if (commonHelpers.isDefined(eventListener)) {
            eventListener();
        }
    }
}
