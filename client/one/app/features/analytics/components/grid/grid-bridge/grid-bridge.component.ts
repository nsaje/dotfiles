import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    OnDestroy,
    OnInit,
    Output,
    SimpleChanges,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
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
import {GRID_API_DEBOUNCE_TIME} from './grid-bridge.component.constants';

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

    context: any;

    private gridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    private onSelectionUpdatedDebouncer$: Subject<void> = new Subject<void>();
    private onSelectionUpdatedHandler: Function;

    constructor(public store: GridBridgeStore) {
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
                if (!commonHelpers.isDefined(this.gridApi)) {
                    return;
                }
                this.gridApi.refreshHeader();
                this.gridApi.refreshCells({
                    columns: [GridColumnTypes.CHECKBOX],
                    force: true,
                });
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
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        if (this.isDataLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }

    private subscribeToStoreStateUpdates() {
        merge(this.createGridUpdater$(), this.createColumnsUpdater$())
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
                    this.handleSelectionUpdate.bind(this)
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
                setTimeout(() => {
                    this.gridApi.sizeColumnsToFit();
                });
            })
        );
    }

    private handleSelectionUpdate(): void {
        this.onSelectionUpdatedDebouncer$.next();
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
