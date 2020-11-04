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
import {CheckboxColumnMapper} from '../mappers/checkbox.mapper';
import {StatsDataColumnMapper} from '../mappers/stats-data.mapper';
import {StatusColumnMapper} from '../mappers/status.mapper';
import {ActionsColumnMapper} from '../mappers/actions.mapper';
import {PerformanceIndicatorColumnMapper} from '../mappers/performance-indicator.mapper';
import {SubmissionStatusColumnMapper} from '../mappers/submission-status.mapper';
import {ExternalLinkColumnMapper} from '../mappers/external-link.mapper';
import {
    BASE_GRID_COLUMN_TYPES,
    EXTERNAL_LINK_COLUMN_TYPES,
} from '../../grid-bridge.component.config';

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
            useClass: ActionsColumnMapper,
        },
        {
            provide: GridColumnTypes.BREAKDOWN,
            useClass: BreakdownColumnMapper,
        },
        {
            provide: GridColumnTypes.STATUS,
            useClass: StatusColumnMapper,
        },
        {
            provide: GridColumnTypes.PERFORMANCE_INDICATOR,
            useClass: PerformanceIndicatorColumnMapper,
        },
        {
            provide: GridColumnTypes.SUBMISSION_STATUS,
            useClass: SubmissionStatusColumnMapper,
        },
        {
            provide: GridColumnTypes.EXTERNAL_LINK,
            useClass: ExternalLinkColumnMapper,
        },
        {
            provide: GridColumnTypes.THUMBNAIL,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.BASE_FIELD,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.EDITABLE_BASE_FIELD,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.BID_MODIFIER_FIELD,
            useClass: StatsDataColumnMapper,
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
