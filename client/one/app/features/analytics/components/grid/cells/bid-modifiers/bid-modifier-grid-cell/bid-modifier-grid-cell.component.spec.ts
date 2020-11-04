import {ComponentFixture, TestBed} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {
    AdGroupAutopilotState,
    AdGroupSettingsAutopilotState,
    BiddingType,
    BidModifierType,
    Breakdown,
    Currency,
    Level,
} from '../../../../../../../app.constants';
import {AuthStore} from '../../../../../../../core/auth/services/auth.store';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';
import {SharedModule} from '../../../../../../../shared/shared.module';
import {Grid} from '../../../grid-bridge/types/grid';
import {GridMeta} from '../../../grid-bridge/types/grid-meta';
import {GridRow} from '../../../grid-bridge/types/grid-row';
import {GridRowDataStatsValue} from '../../../grid-bridge/types/grid-row-data';
import {EditableCellComponent} from '../../editable-cell/editable-cell.component';
import {BidModifierCellComponent} from '../bid-modifier-cell/bid-modifier-cell.component';
import {BidRangeInfoComponent} from '../bid-range-info/bid-range-info.component';
import {BidModifierGridCellComponent} from './bid-modifier-grid-cell.component';
import {BidModifierRendererParams} from './type/bid-modifier.renderer-params';

describe('BidModifierGridCellComponent', () => {
    let component: BidModifierGridCellComponent;
    let fixture: ComponentFixture<BidModifierGridCellComponent>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    let grid: Partial<Grid>;
    let stats: GridRowDataStatsValue;
    let bidModifier: BidModifier;
    let params: Partial<BidModifierRendererParams>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasReadOnlyAccessOn',
        ]);
        authStoreStub.hasReadOnlyAccessOn.and.callFake(() => {
            return false;
        });

        TestBed.configureTestingModule({
            providers: [
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
                },
                {
                    provide: 'zemNavigationNewService',
                    useValue: {
                        getActiveAccount: () => {
                            return {
                                data: {
                                    agencyId: 12345,
                                },
                                id: 12345,
                            };
                        },
                    },
                },
            ],
            declarations: [
                EditableCellComponent,
                BidRangeInfoComponent,
                BidModifierCellComponent,
                BidModifierGridCellComponent,
            ],
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
                        biddingType: BiddingType.CPC,
                        bid: '0',
                        typeSummaries: [],
                        currency: Currency.USD,
                        autopilotState: AdGroupAutopilotState.INACTIVE,
                        agencyUsesRealtimeAutopilot: false,
                    },
                },
            } as GridMeta,
        };

        bidModifier = {
            id: 12345,
            type: BidModifierType.AD,
            target: '0',
            modifier: 0,
        };

        stats = {
            value: bidModifier,
            editMessage: 'You can edit this field',
            isEditable: true,
        };

        params = {
            data: {},
            valueFormatted: stats,
            getGrid: (params: BidModifierRendererParams) => {
                return grid as Grid;
            },
            setBidModifier: (
                bidModifier: BidModifier,
                params: BidModifierRendererParams
            ) => {},
        };
    });

    beforeEach(() => {
        fixture = TestBed.createComponent<BidModifierGridCellComponent>(
            BidModifierGridCellComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
        component.agInit(params as BidModifierRendererParams);

        expect(component.row).toEqual({} as GridRow);
        expect(component.level).toEqual(Level.AD_GROUPS);
        expect(component.breakdown).toEqual(Breakdown.CONTENT_AD);
        expect(component.campaignAutopilot).toBeFalse();
        expect(component.adGroupSettingsAutopilotState).toEqual(
            AdGroupSettingsAutopilotState.INACTIVE
        );
        expect(component.bidModifier).toEqual(bidModifier);
        expect(component.biddingType).toEqual(BiddingType.CPC);
        expect(component.bid).toEqual('0');
        expect(component.bidModifierTypeSummaries).toEqual([]);
        expect(component.entityId).toEqual(12345);
        expect(component.currency).toEqual(Currency.USD);
        expect(component.editMessage).toEqual('You can edit this field');
        expect(component.adGroupAutopilotState).toEqual(
            AdGroupAutopilotState.INACTIVE
        );
        expect(component.agencyUsesRealtimeAutopilot).toBeFalse();
        expect(component.showAutopilotIcon).toBeFalse();
        expect(component.isEditable).toBeTrue();
    });
});
