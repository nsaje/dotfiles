import './grid-bridge.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Inject,
    Input,
    NgZone,
    OnDestroy,
    OnInit,
    Output,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {
    ColumnApi,
    DetailGridInfo,
    DragStoppedEvent,
    GridApi,
    GridColumnsChangedEvent,
    RowDataUpdatedEvent,
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
    SMART_GRID_ROW_ARCHIVED_CLASS,
    GRID_API_DEBOUNCE_TIME,
    GRID_API_LOADING_DATA_ERROR_MESSAGE,
    LOCAL_STORAGE_COLUMNS_KEY,
    LOCAL_STORAGE_NAMESPACE,
} from './grid-bridge.component.constants';
import {NotificationService} from '../../../../../core/notification/services/notification.service';
import {GridRow} from './types/grid-row';
import {Router} from '@angular/router';
import {SmartGridOptions} from '../../../../../shared/components/smart-grid/types/smart-grid-options';
import {LocalStorageService} from '../../../../../core/local-storage/local-storage.service';
import {Breakdown, Level} from '../../../../../app.constants';

@Component({
    selector: 'zem-grid-bridge',
    templateUrl: './grid-bridge.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [GridBridgeStore],
})
export class GridBridgeComponent implements OnInit, OnDestroy {
    @Input()
    grid: Grid;
    @Input()
    isMetaDataReady: boolean = false;
    @Input()
    isDataLoading: boolean = false;
    @Input()
    level: Level;
    @Input()
    breakdown: Breakdown;
    @Output()
    paginationChange = new EventEmitter<PaginationState>();

    gridOptions: SmartGridOptions;
    context: any;

    private gridApi: GridApi;
    private columnApi: ColumnApi;

    private ngUnsubscribe$: Subject<void> = new Subject();

    private onSelectionUpdatedDebouncer$: Subject<void> = new Subject<void>();
    private onSelectionUpdatedHandler: Function;
    private onDataUpdatedErrorHandler: Function;
    private onRowDataUpdatedErrorHandler: Function;

    constructor(
        public store: GridBridgeStore,
        private router: Router,
        private zone: NgZone,
        private notificationService: NotificationService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any,
        private localStorageService: LocalStorageService
    ) {
        this.gridOptions = {
            immutableData: true,
            getRowNodeId: this.getRowNodeId,
            suppressChangeDetection: true,
            applyColumnDefOrder: true,
            enableCellFlashOnColumnsAdd: true,
            rowClassRules: {
                [SMART_GRID_ROW_ARCHIVED_CLASS]: this.isRowArchived.bind(this),
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

        this.store.setGrid(this.grid);
        this.store.setColumnsOrder(this.getColumnsFromLocalStorage());
        this.subscribeToStoreStateUpdates();
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.onSelectionUpdatedHandler)) {
            this.onSelectionUpdatedHandler();
        }
        if (commonHelpers.isDefined(this.onDataUpdatedErrorHandler)) {
            this.onDataUpdatedErrorHandler();
        }
        if (commonHelpers.isDefined(this.onRowDataUpdatedErrorHandler)) {
            this.onRowDataUpdatedErrorHandler();
        }
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        this.columnApi = $event.columnApi;
    }

    onGridColumnsChange($event: GridColumnsChangedEvent) {
        this.setColumnsOrder();
        setTimeout(() => {
            $event.api.sizeColumnsToFit();
        }, 250);
    }

    onDragStop($event: DragStoppedEvent) {
        this.setColumnsOrder();
    }

    onRowDataUpdate($event: RowDataUpdatedEvent) {
        $event.api.refreshCells({
            columns: [GridColumnTypes.ACTIONS],
            force: true,
        });
    }

    navigateByUrl(url: string) {
        this.zone.run(() => {
            this.router.navigateByUrl(url);
        });
    }

    private getRowNodeId(row: GridRow): string {
        return row.id;
    }

    private isRowArchived(params: {data: GridRow}): boolean {
        const row: GridRow = params.data;
        return commonHelpers.getValueOrDefault(row.data?.archived, false);
    }

    private subscribeToStoreStateUpdates() {
        merge(this.createGridUpdater$())
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
                if (
                    commonHelpers.isDefined(this.onRowDataUpdatedErrorHandler)
                ) {
                    this.onRowDataUpdatedErrorHandler();
                }
                this.onDataUpdatedErrorHandler = grid.meta.api.onRowDataUpdatedError(
                    grid.meta.scope,
                    this.handleRowDataUpdateError.bind(this)
                );
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

    private handleRowDataUpdateError(
        $scope: any,
        payload: {
            row: GridRow;
        }
    ) {
        if (!commonHelpers.isDefined(this.gridApi)) {
            return;
        }
        if (
            !commonHelpers.isDefined(payload) ||
            !commonHelpers.isDefined(payload.row)
        ) {
            return;
        }
        const rowNode = this.gridApi.getRowNode(payload.row.id);
        this.gridApi.refreshCells({
            rowNodes: [rowNode],
            force: true,
        });
    }

    private setColumnsOrder() {
        if (
            !commonHelpers.isDefined(this.columnApi) ||
            !commonHelpers.isDefined(this.gridApi)
        ) {
            return;
        }
        const columnsState = this.columnApi.getColumnState();
        const columns = columnsState.map(x => {
            return this.gridApi.getColumnDef(x.colId).field;
        });
        this.store.setColumnsOrder(columns);
        this.saveColumnsToLocalStorage(columns);
    }

    //
    // COLUMNS - LOCAL STORAGE
    //

    private getColumnsFromLocalStorage(): string[] {
        const columnsState =
            this.localStorageService.getItem(
                LOCAL_STORAGE_COLUMNS_KEY,
                LOCAL_STORAGE_NAMESPACE
            ) || {};
        const key = this.getColumnsStateKey();
        return columnsState[key] || [];
    }

    private saveColumnsToLocalStorage(columnsOrder: string[]): void {
        const columnsState =
            this.localStorageService.getItem(
                LOCAL_STORAGE_COLUMNS_KEY,
                LOCAL_STORAGE_NAMESPACE
            ) || {};
        const key = this.getColumnsStateKey();
        this.localStorageService.setItem(
            LOCAL_STORAGE_COLUMNS_KEY,
            {
                ...columnsState,
                [key]: [...columnsOrder],
            },
            LOCAL_STORAGE_NAMESPACE
        );
    }

    private getColumnsStateKey(): string {
        const account: any = this.zemNavigationNewService.getActiveAccount();
        const accountKey: string = commonHelpers.isDefined(account?.id)
            ? account.id.toString()
            : null;

        return [
            ...(commonHelpers.isDefined(accountKey) ? [accountKey] : []),
            ...(commonHelpers.isDefined(this.breakdown)
                ? [this.breakdown]
                : []),
        ].join('.');
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
