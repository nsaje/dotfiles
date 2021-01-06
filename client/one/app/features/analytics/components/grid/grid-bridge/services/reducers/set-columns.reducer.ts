import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
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
import {ThumbnailColumnMapper} from '../mappers/thumbnail.mapper';
import {BidModifierColumnMapper} from '../mappers/bid-modifier.mapper';
import {CurrencyColumnMapper} from '../mappers/currency.mapper';
import {getColumnsInOrder} from '../../helpers/grid-bridge.helpers';

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
            provide: GridColumnTypes.ICON_LINK,
            useClass: ExternalLinkColumnMapper,
        },
        {
            provide: GridColumnTypes.VISIBLE_LINK,
            useClass: ExternalLinkColumnMapper,
        },
        {
            provide: GridColumnTypes.TEXT_LINK,
            useClass: ExternalLinkColumnMapper,
        },
        {
            provide: GridColumnTypes.THUMBNAIL,
            useClass: ThumbnailColumnMapper,
        },
        {
            provide: GridColumnTypes.TEXT,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.PERCENT,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.NUMBER,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.CURRENCY,
            useClass: CurrencyColumnMapper,
        },
        {
            provide: GridColumnTypes.SECONDS,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.DATE_TIME,
            useClass: StatsDataColumnMapper,
        },
        {
            provide: GridColumnTypes.BID_MODIFIER_FIELD,
            useClass: BidModifierColumnMapper,
        },
    ];

    reduce(
        state: GridBridgeStoreState,
        action: SetColumnsAction
    ): GridBridgeStoreState {
        const columns: SmartGridColDef[] = action.payload.map(column => {
            const mapper: ColumnMapper = this.getColumnMapper(column);
            if (commonHelpers.isDefined(mapper)) {
                return mapper.map(state.grid, column);
            }
        });

        return {
            ...state,
            columns: getColumnsInOrder(columns, state.columnsOrder),
        };
    }

    private getColumnMapper(column: GridColumn): ColumnMapper | null {
        const provider = this.providers.find(p => p.provide === column.type);
        if (commonHelpers.isDefined(provider)) {
            return new provider.useClass();
        }
        return null;
    }
}
