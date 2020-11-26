import './grid-bridge.component.less';

import {
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
    ColumnApi,
    DetailGridInfo,
    GridApi,
    GridColumnsChangedEvent,
    GridOptions,
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
export class GridBridgeComponent implements OnInit, OnChanges, OnDestroy {
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
    private onRowDataUpdatedErrorHandler: Function;

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

        this.store.initStore(this.grid);
        this.subscribeToStoreStateUpdates();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (this.gridApi && this.isDataLoading) {
            this.gridApi.showLoadingOverlay();
        }
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
        if (this.isDataLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }

    onGridColumnsChange($event: GridColumnsChangedEvent) {
        if (!commonHelpers.isDefined(this.gridApi)) {
            return;
        }
        setTimeout(() => {
            this.gridApi.sizeColumnsToFit();
        }, 250);
    }

    onRowDataUpdate($event: RowDataUpdatedEvent) {
        if (!commonHelpers.isDefined(this.gridApi)) {
            return;
        }
        this.gridApi.refreshCells({
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
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemGridBridge',
    downgradeComponent({
        component: GridBridgeComponent,
        propagateDigest: false,
    })
);
