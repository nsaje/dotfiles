import {Injector} from '@angular/core';
import {TestBed} from '@angular/core/testing';
import {SmartGridColDef} from '../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {StoreProvider} from '../../../../../../shared/services/store/store.provider';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {
    GridColumnTypes,
    GridRenderingEngineType,
    GridRowLevel,
    GridRowType,
} from '../../../../analytics.constants';
import {Grid} from '../types/grid';
import {GridColumn} from '../types/grid-column';
import {GridColumnOrder} from '../types/grid-column-order';
import {GridBridgeStore} from './grid-bridge.store';
import {GridBridgeStoreState} from './grid-bridge.store.state';
import {
    SetColumnsOrderAction,
    SetColumnsOrderActionReducer,
} from './reducers/set-columns-order.reducer';
import {
    SetColumnsAction,
    SetColumnsActionReducer,
} from './reducers/set-columns.reducer';
import {SetDataAction, SetDataActionReducer} from './reducers/set-data.reducer';
import {SetGridAction, SetGridActionReducer} from './reducers/set-grid.reducer';

class SetTestColumnsActionReducer extends SetColumnsActionReducer {
    reduce(
        state: GridBridgeStoreState,
        action: SetColumnsAction
    ): GridBridgeStoreState {
        return {
            ...state,
            columns: action.payload.map(column => this.map(column)),
        };
    }

    private map(column: GridColumn): SmartGridColDef {
        return {
            headerName: column.data.name,
            field: column.data.field,
        };
    }
}

// tslint:disable-next-line: max-classes-per-file
class TestGridBridgeStore extends GridBridgeStore {
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
                useClass: SetTestColumnsActionReducer,
            },
            {
                provide: SetDataAction,
                useClass: SetDataActionReducer,
            },
            {
                provide: SetColumnsOrderAction,
                useClass: SetColumnsOrderActionReducer,
            },
        ];
    }
}

describe('GridBridgeStore', () => {
    let store: TestGridBridgeStore;
    let mockedGrid: Grid;
    let mockedVisibleColumns: GridColumn[];

    beforeEach(() => {
        store = new TestGridBridgeStore(TestBed.get(Injector));

        mockedVisibleColumns = [
            {
                type: GridColumnTypes.TEXT,
                field: '',
                data: {
                    name: 'Test',
                    field: 'test_field',
                    internal: false,
                    shown: true,
                    totalRow: true,
                    type: GridColumnTypes.TEXT,
                },
                visible: true,
                disabled: false,
                order: GridColumnOrder.DESC,
            },
        ];
        mockedGrid = {
            header: {
                columns: [],
            },
            body: {
                rows: [
                    {
                        id: 'row',
                        type: GridRowType.STATS,
                        entity: null,
                        data: {
                            stats: {
                                test_field: {
                                    value: 'TEST VALUE',
                                },
                            },
                        },
                        level: GridRowLevel.BASE,
                        parent: null,
                        collapsed: true,
                        visible: true,
                    },
                ],
                pagination: {
                    complete: true,
                    offset: 0,
                    limit: 1,
                    count: 1,
                },
            },
            footer: {
                row: {
                    id: 'totals',
                    type: GridRowType.STATS,
                    entity: null,
                    data: {
                        stats: {
                            test_field: {
                                value: 'TOTALS OF TEST VALUE',
                            },
                        },
                    },
                    level: GridRowLevel.BASE,
                    parent: null,
                    collapsed: true,
                    visible: true,
                },
            },
            meta: {
                initialized: true,
                loading: false,
                renderingEngine: GridRenderingEngineType.SMART_GRID,
                paginationOptions: {type: 'server', page: 1, pageSize: 10},
                options: null,
                api: {
                    onColumnsUpdated: (scope: any, handlerFn: Function) => {
                        handlerFn();
                    },
                    onDataUpdated: (scope: any, handlerFn: Function) => {
                        handlerFn();
                    },
                    onRowDataUpdated: (scope: any, handlerFn: Function) => {
                        handlerFn();
                    },
                    onRowDataUpdatedError: (
                        scope: any,
                        handlerFn: Function
                    ) => {
                        handlerFn();
                    },
                    getVisibleColumns: () => {
                        return mockedVisibleColumns;
                    },
                },
                dataService: null,
                columnsService: null,
                orderService: null,
                collapseService: null,
                selectionService: null,
                pubsub: null,
                data: null,
                scope: null,
            },
        };
    });

    it('should correctly reduce grid', () => {
        expect(store.state.grid).toEqual(null);
        store.setGrid(mockedGrid);
        expect(store.state.grid).toEqual(mockedGrid);
    });

    it('should correctly reduce grid columns', () => {
        store.setGrid(mockedGrid);
        store.connect();
        expect(store.state.columns).toEqual([
            {
                headerName: 'Test',
                field: 'test_field',
            },
        ]);
    });

    it('should correctly reduce grid data', () => {
        store.setGrid(mockedGrid);
        store.connect();
        expect(store.state.data).toEqual({
            rows: [
                {
                    id: 'row',
                    type: GridRowType.STATS,
                    entity: null,
                    data: {
                        stats: {
                            test_field: {
                                value: 'TEST VALUE',
                            },
                        },
                    },
                    level: GridRowLevel.BASE,
                    parent: null,
                    collapsed: true,
                    visible: true,
                },
            ] as any[],
            totals: [
                {
                    id: 'totals',
                    type: GridRowType.STATS,
                    entity: null,
                    data: {
                        stats: {
                            test_field: {
                                value: 'TOTALS OF TEST VALUE',
                            },
                        },
                    },
                    level: GridRowLevel.BASE,
                    parent: null,
                    collapsed: true,
                    visible: true,
                },
            ] as any[],
            paginationOptions: {
                type: 'server',
                page: 1,
                pageSize: 10,
            },
            pagination: {
                complete: true,
                offset: 0,
                limit: 1,
                count: 1,
            },
        });
    });

    it('should correctly reduce grid columns order', () => {
        const mockedColumns: string[] = ['one', 'three', 'two'];
        store.setColumnsOrder(mockedColumns);
        expect(store.state.columnsOrder).toEqual(['one', 'three', 'two']);
    });
});
