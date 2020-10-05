import {ColDef} from 'ag-grid-community';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {ColumnMapper} from '../mappers/column.mapper';
import {ColumnMapperProvider} from '../mappers/column.provider';
import {SetColumnsAction, SetColumnsActionReducer} from './set-columns.reducer';

class TestColumnMapper extends ColumnMapper {
    map(grid: Grid, column: GridColumn): ColDef {
        return {
            headerName: column.data.name,
            field: column.data.field,
        };
    }
}

// tslint:disable-next-line: max-classes-per-file
class TestSetColumnsActionReducer extends SetColumnsActionReducer {
    readonly providers: ColumnMapperProvider<
        GridColumnTypes,
        ColumnMapper
    >[] = [
        {
            provide: GridColumnTypes.BASE_FIELD,
            useClass: TestColumnMapper,
        },
    ];
}

describe('SetColumnsActionReducer', () => {
    let reducer: TestSetColumnsActionReducer;
    let mockedColumns: GridColumn[];

    beforeEach(() => {
        reducer = new TestSetColumnsActionReducer();
        mockedColumns = [
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
                order: 'none',
            },
        ];
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new GridBridgeStoreState(),
            new SetColumnsAction(mockedColumns)
        );

        expect(state.columns).toEqual([
            {
                headerName: 'Test',
                field: 'test_field',
            },
        ]);
    });
});
