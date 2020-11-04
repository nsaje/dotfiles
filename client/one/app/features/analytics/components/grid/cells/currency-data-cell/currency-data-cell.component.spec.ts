import {ComponentFixture, TestBed} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {
    AdGroupAutopilotState,
    AdGroupSettingsAutopilotState,
    Breakdown,
    Currency,
    Level,
} from '../../../../../../app.constants';
import {SharedModule} from '../../../../../../shared/shared.module';
import {Grid} from '../../grid-bridge/types/grid';
import {GridMeta} from '../../grid-bridge/types/grid-meta';
import {GridRow} from '../../grid-bridge/types/grid-row';
import {GridRowDataStatsValue} from '../../grid-bridge/types/grid-row-data';
import {EditableCellComponent} from '../editable-cell/editable-cell.component';
import {
    EditableCellMode,
    EditableCellPlacement,
} from '../editable-cell/editable-cell.constants';
import {CurrencyDataCellComponent} from './currency-data-cell.component';
import {CurrencyDataRendererParams} from './type/currency-data.renderer-params';

describe('CurrencyDataCellComponent', () => {
    let component: CurrencyDataCellComponent;
    let fixture: ComponentFixture<CurrencyDataCellComponent>;

    let grid: Partial<Grid>;
    let stats: GridRowDataStatsValue;
    let params: Partial<CurrencyDataRendererParams>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [EditableCellComponent, CurrencyDataCellComponent],
            imports: [FormsModule, SharedModule],
        });

        grid = {
            meta: {
                data: {
                    id: 12345,
                    level: Level.AD_GROUPS,
                    breakdown: Breakdown.CONTENT_AD,
                    campaignAutopilot: false,
                    adGroupAutopilotState:
                        AdGroupSettingsAutopilotState.INACTIVE,
                    ext: {
                        currency: Currency.USD,
                        autopilotState: AdGroupAutopilotState.INACTIVE,
                        agencyUsesRealtimeAutopilot: false,
                    },
                },
            } as GridMeta,
        };

        stats = {
            value: '10',
            editMessage: 'You can edit this field',
            isEditable: true,
        };

        params = {
            data: {},
            value: stats,
            valueFormatted: '$10.00',
            getGrid: (params: CurrencyDataRendererParams) => {
                return grid as Grid;
            },
            setCurrencyData: (
                value: string,
                params: CurrencyDataRendererParams
            ) => {},
        };
    });

    beforeEach(() => {
        fixture = TestBed.createComponent<CurrencyDataCellComponent>(
            CurrencyDataCellComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
        component.agInit(params as CurrencyDataRendererParams);

        expect(component.grid).toEqual(grid as Grid);
        expect(component.row).toEqual({} as GridRow);
        expect(component.level).toEqual(Level.AD_GROUPS);
        expect(component.breakdown).toEqual(Breakdown.CONTENT_AD);
        expect(component.campaignAutopilot).toBeFalse();
        expect(component.adGroupSettingsAutopilotState).toEqual(
            AdGroupSettingsAutopilotState.INACTIVE
        );
        expect(component.valueFormatted).toEqual('$10.00');
        expect(component.originalValue).toEqual('10');
        expect(component.value).toEqual('10');
        expect(component.currency).toEqual(Currency.USD);
        expect(component.currencySymbol).toEqual('$');
        expect(component.editMessage).toEqual('You can edit this field');
        expect(component.showAutopilotIcon).toBeFalse();
        expect(component.isEditable).toBeTrue();
        expect(component.isSaveInProgress).toBeFalse();
        expect(component.mode).toEqual(EditableCellMode.READ);
        expect(component.placement).toEqual(EditableCellPlacement.IN_LINE);
    });
});
