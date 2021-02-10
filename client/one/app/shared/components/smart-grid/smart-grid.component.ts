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
    OnDestroy,
    ChangeDetectorRef,
} from '@angular/core';
import {
    DetailGridInfo,
    GridApi,
    RowSelectedEvent,
    SelectionChangedEvent,
    GridSizeChangedEvent,
    FirstDataRenderedEvent,
    GridColumnsChangedEvent,
    RowDataChangedEvent,
    RowDataUpdatedEvent,
    ColumnApi,
    Column,
    ColumnState,
    DragStoppedEvent,
    DragStartedEvent,
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
import {isDefined} from '../../helpers/common.helpers';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {SmartGridColDef} from './types/smart-grid-col-def';
import {distinct} from '../../helpers/array.helpers';
import {SmartGridOptions} from './types/smart-grid-options';

@Component({
    selector: 'zem-smart-grid',
    templateUrl: './smart-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SmartGridComponent implements OnInit, OnChanges, OnDestroy {
    @Input('gridOptions')
    options: SmartGridOptions;
    @Input()
    columnDefs: SmartGridColDef[];
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
    @Input()
    isLoading: boolean = false;
    @Output()
    rowSelected = new EventEmitter<any>();
    @Output()
    selectionChange = new EventEmitter<any[]>();
    @Output()
    gridReady = new EventEmitter<DetailGridInfo>();
    @Output()
    gridSizeChange = new EventEmitter<GridSizeChangedEvent>();
    @Output()
    firstDataRender = new EventEmitter<FirstDataRenderedEvent>();
    @Output()
    gridColumnsChange = new EventEmitter<GridColumnsChangedEvent>();
    @Output()
    rowDataChange = new EventEmitter<RowDataChangedEvent>();
    @Output()
    rowDataUpdate = new EventEmitter<RowDataUpdatedEvent>();
    @Output()
    dragStart = new EventEmitter<DragStartedEvent>();
    @Output()
    dragStop = new EventEmitter<DragStoppedEvent>();
    @Output()
    paginationChange = new EventEmitter<PaginationState>();

    isGridReady: boolean;
    gridOptions: SmartGridOptions;
    gridApi: GridApi;

    paginationPage: number;
    paginationPageSize: number;
    paginationPageSizeOptions: PageSizeConfig[];

    hideHorizontalScroll: boolean = false;

    private gridWidth$: Subject<number> = new Subject<number>();
    private ngUnsubscribe$: Subject<void> = new Subject();

    private previousColumnStateCache: ColumnState[] = [];
    private columnStateCache: ColumnState[] = [];

    constructor(private changeDetectorRef: ChangeDetectorRef) {}

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

        if (changes.isLoading && this.gridApi) {
            this.toggleLoading();
        }
    }

    ngOnDestroy(): void {
        this.previousColumnStateCache = null;
        this.columnStateCache = null;
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onRowSelected($event: RowSelectedEvent) {
        this.rowSelected.emit($event.data);
    }

    onSelectionChanged($event: SelectionChangedEvent) {
        this.selectionChange.emit($event.api.getSelectedRows());
    }

    onGridReady(params: DetailGridInfo) {
        this.isGridReady = true;
        this.gridApi = params.api;
        this.toggleLoading();
        this.gridReady.emit(params);

        if (
            params.columnApi
                .getAllColumns()
                .some(this.columnUnpinsBelowGridWidth)
        ) {
            this.setupPinnedColumnToggling(params.columnApi);
        }
    }

    onGridSizeChanged($event: GridSizeChangedEvent) {
        this.gridSizeChange.emit($event);
        if (this.isGridReady) {
            setTimeout(() => {
                this.gridApi.sizeColumnsToFit();
            }, 250);

            this.gridWidth$.next($event.clientWidth);
        }
    }

    onFirstDataRendered($event: FirstDataRenderedEvent) {
        this.firstDataRender.emit($event);
        if (this.isGridReady) {
            setTimeout(() => {
                this.gridApi.sizeColumnsToFit();
            }, 250);
        }
    }

    onGridColumnsChanged($event: GridColumnsChangedEvent) {
        this.previousColumnStateCache = [...this.columnStateCache];
        this.columnStateCache = [...$event.columnApi.getColumnState()];
        this.gridColumnsChange.emit($event);
        if (this.gridOptions.enableCellFlashOnColumnsAdd) {
            setTimeout(() => {
                this.handleCellFlashOnColumnsAdd();
            }, 250);
        }
    }

    onRowDataChanged($event: RowDataChangedEvent) {
        this.rowDataChange.emit($event);
    }

    onRowDataUpdated($event: RowDataUpdatedEvent) {
        this.rowDataUpdate.emit($event);
    }

    onDragStarted($event: DragStartedEvent) {
        this.dragStart.emit($event);
    }

    onDragStopped($event: DragStoppedEvent) {
        this.dragStop.emit($event);
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

    private columnUnpinsBelowGridWidth(column: Column): boolean {
        return (
            isDefined(column.getPinned()) &&
            isDefined(
                (<SmartGridColDef>column.getUserProvidedColDef())
                    .unpinBelowGridWidth
            )
        );
    }

    private countThresholdsAboveWidth(
        widthThresholds: number[],
        width: number
    ): number {
        return widthThresholds.filter(threshold => width < threshold).length;
    }

    private setupPinnedColumnToggling(columnApi: ColumnApi) {
        const columnPinnedSettings: {
            colId: string;
            pinned: string;
            unpinBelowGridWidth: number;
        }[] = columnApi
            .getAllColumns()
            .filter(this.columnUnpinsBelowGridWidth)
            .map(column => ({
                colId: column.getColId(),
                pinned: column.getPinned(),
                unpinBelowGridWidth: (<SmartGridColDef>(
                    column.getUserProvidedColDef()
                )).unpinBelowGridWidth,
            }));

        const widthThresholds: number[] = distinct(
            columnPinnedSettings.map(setting => setting.unpinBelowGridWidth)
        );

        this.gridWidth$
            .pipe(
                debounceTime(100),
                distinctUntilChanged(
                    (prev, curr) =>
                        this.countThresholdsAboveWidth(
                            widthThresholds,
                            prev
                        ) ===
                        this.countThresholdsAboveWidth(widthThresholds, curr)
                ),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(gridWidth =>
                columnPinnedSettings.forEach(setting => {
                    const pinColumn: string | null =
                        gridWidth < setting.unpinBelowGridWidth
                            ? null
                            : setting.pinned;
                    columnApi.setColumnPinned(setting.colId, pinColumn);
                })
            );
    }

    private handleCellFlashOnColumnsAdd() {
        if (arrayHelpers.isEmpty(this.previousColumnStateCache)) {
            return;
        }

        const colIds = this.columnStateCache
            .map(column => column.colId)
            .filter(
                colId =>
                    !this.previousColumnStateCache
                        .map(p => p.colId)
                        .includes(colId)
            );
        if (!arrayHelpers.isEmpty(colIds)) {
            this.gridApi.ensureColumnVisible(colIds[colIds.length - 1]);
            this.gridApi.flashCells({
                columns: colIds,
            });
        }
    }

    private toggleLoading() {
        if (this.isLoading) {
            this.hideHorizontalScroll = true;
            this.gridApi.showLoadingOverlay();
        } else {
            setTimeout(() => {
                this.hideHorizontalScroll = false;
                this.changeDetectorRef.markForCheck();
            }, 250);
        }
    }
}
