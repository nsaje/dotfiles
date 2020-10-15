import {ColDef} from 'ag-grid-community';
import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {ColumnMapper} from '../mappers/column.mapper';
import {ColumnMapperProvider} from '../mappers/column.provider';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridColumn} from '../../types/grid-column';
import {BreakdownColumnMapper} from '../mappers/breakdown.mapper';
import {
    BASE_GRID_COLUMN_TYPES,
    EXTERNAL_LINK_COLUMN_TYPES,
} from '../../../../../analytics.config';
import {CheckboxColumnMapper} from '../mappers/checkbox.mapper';
import {TextColumnMapper} from '../mappers/text.mapper';

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
            provide: GridColumnTypes.CHECKBOX,
            useClass: CheckboxColumnMapper,
        },
        {
            provide: GridColumnTypes.ACTIONS,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.BREAKDOWN,
            useClass: BreakdownColumnMapper,
        },
        {
            provide: GridColumnTypes.BASE_FIELD,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.EDITABLE_BASE_FIELD,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.STATUS,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.SUBMISSION_STATUS,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.PERFORMANCE_INDICATOR,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.EXTERNAL_LINK,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.THUMBNAIL,
            useClass: TextColumnMapper,
        },
        {
            provide: GridColumnTypes.BID_MODIFIER_FIELD,
            useClass: TextColumnMapper,
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
