import './grid-bridge.component.less';

import {
    AfterViewInit,
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Inject,
    Input,
    NgZone,
    OnChanges,
    OnDestroy,
    OnInit,
    Output,
    SimpleChanges,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {
    ColDef,
    ColumnApi,
    DetailGridInfo,
    GridApi,
    GridOptions,
    GridSizeChangedEvent,
} from 'ag-grid-community';
import {merge, Observable, Subject} from 'rxjs';
import {
    debounceTime,
    distinctUntilChanged,
    map,
    takeUntil,
    tap,
} from 'rxjs/operators';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {GridBridgeStore} from './services/grid-bridge.store';
import {Grid} from './types/grid';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';
import {GridColumnTypes} from '../../../analytics.constants';
import {
    ARCHIVED_ROW_CLASS,
    GRID_API_DEBOUNCE_TIME,
    GRID_API_LOADING_DATA_ERROR_MESSAGE,
    TABLET_BREAKPOINT,
} from './grid-bridge.component.constants';
import {NotificationService} from '../../../../../core/notification/services/notification.service';
import {DOCUMENT} from '@angular/common';
import {GridRow} from './types/grid-row';
import {Router} from '@angular/router';

@Component({
    selector: 'zem-grid-bridge',
    templateUrl: './grid-bridge.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [GridBridgeStore],
})
export class GridBridgeComponent
    implements OnInit, OnChanges, AfterViewInit, OnDestroy {
    @Input()
    grid: Grid;
    @Input()
    isMetaDataReady: boolean = false;
    @Input()
    isDataLoading: boolean = false;
    @Output()
    paginationChange = new EventEmitter<PaginationState>();

    gridOptions: GridOptions;
    context: any;

    private gridApi: GridApi;
    private columnApi: ColumnApi;

    private ngUnsubscribe$: Subject<void> = new Subject();

    private onSelectionUpdatedDebouncer$: Subject<void> = new Subject<void>();
    private onSelectionUpdatedHandler: Function;
    private onDataUpdatedErrorHandler: Function;

    private sidebarContainerContentElement: Element;

    constructor(
        public store: GridBridgeStore,
        private router: Router,
        private zone: NgZone,
        @Inject(DOCUMENT) private document: Document,
        private notificationService: NotificationService
    ) {
        this.gridOptions = {
            immutableData: true,
            getRowNodeId: this.getRowNodeId,
            suppressChangeDetection: true,
            rowClassRules: {
                [ARCHIVED_ROW_CLASS]: (params: {data: GridRow}) => {
                    const row: GridRow = params.data;
                    return commonHelpers.getValueOrDefault(
                        row.data?.archived,
                        false
                    );
                },
            },
        };
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit(): void {
        this.onSelectionUpdatedDebouncer$
            .pipe(
                debounceTime(GRID_API_DEBOUNCE_TIME),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(() => {
                this.handleSelectionUpdate();
            });

        this.store.initStore(this.grid);
        this.subscribeToStoreStateUpdates();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (this.gridApi && this.isDataLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }

    ngAfterViewInit(): void {
        this.sidebarContainerContentElement = this.document.getElementById(
            'zem-sidebar-container__content'
        );
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.onSelectionUpdatedHandler)) {
            this.onSelectionUpdatedHandler();
        }
        if (commonHelpers.isDefined(this.onDataUpdatedErrorHandler)) {
            this.onDataUpdatedErrorHandler();
        }
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        this.columnApi = $event.columnApi;
        if (this.isDataLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }

    onGridSizeChange($event: GridSizeChangedEvent) {
        this.setBreakdownColumnPinnedProperty();
    }

    navigateByUrl(url: string) {
        this.zone.run(() => {
            this.router.navigateByUrl(url);
        });
    }

    private getRowNodeId(row: GridRow): string {
        return row.id;
    }

    private subscribeToStoreStateUpdates() {
        merge(
            this.createGridUpdater$(),
            this.createColumnsUpdater$(),
            this.createRowUpdater$()
        )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createGridUpdater$(): Observable<Grid> {
        return this.store.state$.pipe(
            map(state => state.grid),
            distinctUntilChanged(),
            tap(grid => {
                this.store.connect();
                if (commonHelpers.isDefined(this.onSelectionUpdatedHandler)) {
                    this.onSelectionUpdatedHandler();
                }
                this.onSelectionUpdatedHandler = grid.meta.api.onSelectionUpdated(
                    grid.meta.scope,
                    () => this.onSelectionUpdatedDebouncer$.next()
                );
                if (commonHelpers.isDefined(this.onDataUpdatedErrorHandler)) {
                    this.onDataUpdatedErrorHandler();
                }
                this.onDataUpdatedErrorHandler = grid.meta.api.onDataUpdatedError(
                    grid.meta.scope,
                    this.handleDataUpdateError.bind(this)
                );
            })
        );
    }

    private createColumnsUpdater$(): Observable<ColDef[]> {
        return this.store.state$.pipe(
            map(state => state.columns),
            distinctUntilChanged(),
            tap(() => {
                if (!commonHelpers.isDefined(this.gridApi)) {
                    return;
                }
                this.setBreakdownColumnPinnedProperty();
                setTimeout(() => {
                    this.gridApi.sizeColumnsToFit();
                }, 500);
            })
        );
    }

    private createRowUpdater$(): Observable<GridRow[]> {
        return this.store.state$.pipe(
            map(state => state.data.rows),
            distinctUntilChanged(),
            tap(() => {
                if (!commonHelpers.isDefined(this.gridApi)) {
                    return;
                }
                this.gridApi.refreshCells({
                    columns: [GridColumnTypes.ACTIONS],
                    force: true,
                });
            })
        );
    }

    private handleSelectionUpdate(): void {
        if (!commonHelpers.isDefined(this.gridApi)) {
            return;
        }
        this.gridApi.refreshHeader();
        this.gridApi.refreshCells({
            columns: [GridColumnTypes.CHECKBOX],
            force: true,
        });
    }

    private handleDataUpdateError(): void {
        if (!commonHelpers.isDefined(this.gridApi)) {
            return;
        }
        this.gridApi.hideOverlay();
        this.gridApi.showNoRowsOverlay();
        this.notificationService.error(GRID_API_LOADING_DATA_ERROR_MESSAGE);
    }

    private setBreakdownColumnPinnedProperty(): void {
        if (!commonHelpers.isDefined(this.columnApi)) {
            return;
        }
        if (!commonHelpers.isDefined(this.sidebarContainerContentElement)) {
            return;
        }
        const column = this.columnApi.getColumn(GridColumnTypes.BREAKDOWN);
        if (!commonHelpers.isDefined(column)) {
            return;
        }

        const clientWidth = this.sidebarContainerContentElement.clientWidth;
        if (clientWidth > TABLET_BREAKPOINT) {
            if (!column.isPinned()) {
                this.columnApi.setColumnPinned(column.getId(), 'left');
            }
        } else {
            if (column.isPinned()) {
                this.columnApi.setColumnPinned(column.getId(), null);
            }
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemGridBridge',
    downgradeComponent({
        component: GridBridgeComponent,
        propagateDigest: false,
    })
);
