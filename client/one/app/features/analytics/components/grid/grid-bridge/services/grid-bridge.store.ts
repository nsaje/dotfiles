import {Injectable, Injector, OnDestroy} from '@angular/core';
import {Store} from '../../../../../../shared/services/store/store';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {StoreProvider} from '../../../../../../shared/services/store/store.provider';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {Grid} from '../types/grid';
import {GridColumn} from '../types/grid-column';
import {GridBridgeStoreState} from './grid-bridge.store.state';
import {
    SetColumnsAction,
    SetColumnsActionReducer,
} from './reducers/set-columns.reducer';
import {SetDataAction, SetDataActionReducer} from './reducers/set-data.reducer';
import {SetGridAction, SetGridActionReducer} from './reducers/set-grid.reducer';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {Subject} from 'rxjs';
import {debounceTime, takeUntil} from 'rxjs/operators';
import {GRID_API_DEBOUNCE_TIME} from '../grid-bridge.component.constants';

@Injectable()
export class GridBridgeStore extends Store<GridBridgeStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();

    private onColumnsUpdatedDebouncer$: Subject<void> = new Subject<void>();
    private onColumnsUpdatedHandler: Function;

    private onDataUpdatedDebouncer$: Subject<void> = new Subject<void>();
    private onDataUpdatedHandler: Function;

    constructor(injector: Injector) {
        super(new GridBridgeStoreState(), injector);
    }

    ngOnDestroy() {
        super.ngOnDestroy();
        if (commonHelpers.isDefined(this.onColumnsUpdatedHandler)) {
            this.onColumnsUpdatedHandler();
        }
        if (commonHelpers.isDefined(this.onDataUpdatedHandler)) {
            this.onDataUpdatedHandler();
        }
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<GridBridgeStoreState, StoreAction<any>>
        | StoreEffect<GridBridgeStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetGridAction,
                useClass: SetGridActionReducer,
            },
            {
                provide: SetColumnsAction,
                useClass: SetColumnsActionReducer,
            },
            {
                provide: SetDataAction,
                useClass: SetDataActionReducer,
            },
        ];
    }

    initStore(grid: Grid): void {
        this.onColumnsUpdatedDebouncer$
            .pipe(
                debounceTime(GRID_API_DEBOUNCE_TIME),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(() => {
                const api: any = this.state.grid.meta.api;
                const columns: GridColumn[] = api.getVisibleColumns();
                this.dispatch(new SetColumnsAction(columns));
            });
        this.onDataUpdatedDebouncer$
            .pipe(
                debounceTime(GRID_API_DEBOUNCE_TIME),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(() => {
                this.dispatch(new SetDataAction(this.state.grid));
            });

        this.dispatch(new SetGridAction(grid));
    }

    connect(): void {
        const api: any = this.state.grid.meta.api;
        const scope: any = this.state.grid.meta.scope;

        this.onColumnsUpdatedHandler = api.onColumnsUpdated(
            scope,
            this.handleColumnsUpdate.bind(this)
        );
        this.onDataUpdatedHandler = api.onDataUpdated(
            scope,
            this.handleDataUpdate.bind(this)
        );
    }

    private handleColumnsUpdate(): void {
        this.onColumnsUpdatedDebouncer$.next();
    }

    private handleDataUpdate(): void {
        this.onDataUpdatedDebouncer$.next();
    }
}
