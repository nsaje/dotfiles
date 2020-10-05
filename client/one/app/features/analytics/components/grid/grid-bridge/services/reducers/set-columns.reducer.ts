import {ColDef} from 'ag-grid-community';
import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {ColumnMapper} from '../mappers/column.mapper';
import {ColumnMapperProvider} from '../mappers/column.provider';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridColumn} from '../../types/grid-column';
import {StringColumnMapper} from '../mappers/string.mapper';
import {
    BASE_GRID_COLUMN_TYPES,
    EXTERNAL_LINK_COLUMN_TYPES,
} from '../../../../../analytics.config';

export class SetColumnsAction extends StoreAction<GridColumn[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetColumnsActionReducer extends StoreReducer<
    GridBridgeStoreState,
    SetColumnsAction
> {
    readonly providers: ColumnMapperProvider<
        GridColumnTypes,
        ColumnMapper
    >[] = [
        {
            provide: GridColumnTypes.BREAKDOWN,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.ACTIONS,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.CHECKBOX,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.STATUS,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.SUBMISSION_STATUS,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.PERFORMANCE_INDICATOR,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.EXTERNAL_LINK,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.EDITABLE_BASE_FIELD,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.BASE_FIELD,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.THUMBNAIL,
            useClass: StringColumnMapper,
        },
        {
            provide: GridColumnTypes.BID_MODIFIER_FIELD,
            useClass: StringColumnMapper,
        },
    ];

    reduce(
        state: GridBridgeStoreState,
        action: SetColumnsAction
    ): GridBridgeStoreState {
        const columns: ColDef[] = action.payload.map(column => {
            const mapper: ColumnMapper = this.getColumnMapper(column);
            if (commonHelpers.isDefined(mapper)) {
                return mapper.map(state.grid, column);
            }
        });

        return {
            ...state,
            columns: columns,
        };
    }

    private getColumnMapper(column: GridColumn): ColumnMapper | null {
        const gridColumnType = this.getGridColumnType(column);
        const provider = this.providers.find(p => p.provide === gridColumnType);
        if (commonHelpers.isDefined(provider)) {
            return new provider.useClass();
        }
        return null;
    }

    private getGridColumnType(column: GridColumn): GridColumnTypes {
        const gridColumnType = column.type || GridColumnTypes.BASE_FIELD;

        if (BASE_GRID_COLUMN_TYPES.includes(gridColumnType)) {
            if (
                commonHelpers.isDefined(column.data) &&
                commonHelpers.getValueOrDefault(column.data.editable, false)
            ) {
                return GridColumnTypes.EDITABLE_BASE_FIELD;
            }
            return GridColumnTypes.BASE_FIELD;
        }

        if (EXTERNAL_LINK_COLUMN_TYPES.includes(gridColumnType)) {
            return GridColumnTypes.EXTERNAL_LINK;
        }

        return gridColumnType;
    }
}
