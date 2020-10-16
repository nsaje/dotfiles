import {BidRangeInfoStore} from './bid-range-info.store';
import {
    BidModifierType,
    BiddingType,
    Currency,
    AdGroupAutopilotState,
} from '../../../../../../../../app.constants';
import {BidModifier} from '../../../../../../../../core/bid-modifiers/types/bid-modifier';
import {BidModifierTypeSummary} from '../../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';

describe('BidRangeInfoStore', () => {
    let store: BidRangeInfoStore;
    let bidModifier: BidModifier;
    let biddingType: BiddingType;
    let bid: string;
    let bidModifierTypeSummaries: BidModifierTypeSummary[];
    let currency: Currency;
    let fractionSize: number;
    let adGroupAutopilotState: AdGroupAutopilotState;
    let modifierPercent: string;
    let agencyUsesRealtimeAutopilot: boolean;

    beforeEach(() => {
        store = new BidRangeInfoStore();
        bidModifier = {
            type: BidModifierType.DEVICE,
            target: 'MOBILE',
            modifier: 1.1,
        } as BidModifier;
        biddingType = BiddingType.CPC;
        bid = '1.0';
        bidModifierTypeSummaries = [
            {
                type: BidModifierType.DEVICE,
                count: 2,
                min: 0.9,
                max: 1.1,
            } as BidModifierTypeSummary,
            {
                type: BidModifierType.SOURCE,
                count: 4,
                min: 0.8,
                max: 1.2,
            } as BidModifierTypeSummary,
        ] as BidModifierTypeSummary[];
        currency = Currency.USD;
        fractionSize = 4;
        adGroupAutopilotState = AdGroupAutopilotState.INACTIVE;
        modifierPercent = null;
        agencyUsesRealtimeAutopilot = true;
    });

    it('should correctly store inputs into state', () => {
        bidModifierTypeSummaries = [] as BidModifierTypeSummary[];

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );

        expect(store.state.bidModifier).toEqual(bidModifier);
        expect(store.state.biddingType).toEqual(biddingType);
        expect(store.state.bid).toEqual(bid);
        expect(store.state.bidModifierTypeSummaries).toEqual(
            bidModifierTypeSummaries
        );
        expect(store.state.currency).toEqual(currency);
        expect(store.state.fractionSize).toEqual(fractionSize);
        expect(store.state.adGroupAutopilotState).toEqual(
            adGroupAutopilotState
        );
        expect(store.state.agencyUsesRealtimeAutopilot).toEqual(
            agencyUsesRealtimeAutopilot
        );
    });

    it('should correctly present bid range info for CPC / device / inactive autopilot / no selected dimensions', () => {
        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );

        expect(store.state.bidModifierTypeSummaries).toEqual([
            {
                type: BidModifierType.SOURCE,
                count: 4,
                min: 0.8,
                max: 1.2,
            } as BidModifierTypeSummary,
        ]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual(null);
        expect(store.state.autopilot).toEqual(false);
        expect(store.state.minFactor).toEqual(1.0);
        expect(store.state.maxFactor).toEqual(1.0);
        expect(store.state.computedBidMin).toEqual('$1.1000');
        expect(store.state.computedBidMax).toEqual('$1.1000');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the target bid CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$1.1000 - $1.1000');
    });

    it('should correctly present bid range info for CPM / device / inactive autopilot / no selected dimensions', () => {
        biddingType = BiddingType.CPM;

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );

        expect(store.state.bidModifierTypeSummaries).toEqual([
            {
                type: BidModifierType.SOURCE,
                count: 4,
                min: 0.8,
                max: 1.2,
            } as BidModifierTypeSummary,
        ]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual(null);
        expect(store.state.autopilot).toEqual(false);
        expect(store.state.minFactor).toEqual(1.0);
        expect(store.state.maxFactor).toEqual(1.0);
        expect(store.state.computedBidMin).toEqual('$1.1000');
        expect(store.state.computedBidMax).toEqual('$1.1000');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPM is determined by the target bid CPM set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPM range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPM:');
        expect(store.state.formattedBidValueRange).toEqual('$1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPM range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$1.1000 - $1.1000');
    });

    it('should correctly present bid range info for CPC / source / inactive autopilot / no selected dimensions', () => {
        bidModifier = {
            type: BidModifierType.SOURCE,
            target: 'example.com',
            modifier: 0.9,
        } as BidModifier;

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );

        expect(store.state.bidModifierTypeSummaries).toEqual([
            {
                type: BidModifierType.DEVICE,
                count: 2,
                min: 0.9,
                max: 1.1,
            } as BidModifierTypeSummary,
        ]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual(null);
        expect(store.state.autopilot).toEqual(false);
        expect(store.state.minFactor).toEqual(1.0);
        expect(store.state.maxFactor).toEqual(1.0);
        expect(store.state.computedBidMin).toEqual('$0.9000');
        expect(store.state.computedBidMax).toEqual('$0.9000');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the target bid CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.9000 - $0.9000');
    });

    it('should correctly present bid range info for CPC / device / inactive autopilot / selected all dimensions', () => {
        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );
        store.updateSelectedGridRows(store.state.bidModifierTypeGridRows);

        expect(store.state.bidModifierTypeSummaries).toEqual([
            {
                type: BidModifierType.SOURCE,
                count: 4,
                min: 0.8,
                max: 1.2,
            } as BidModifierTypeSummary,
        ]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual(null);
        expect(store.state.autopilot).toEqual(false);
        expect(store.state.minFactor).toEqual(0.8);
        expect(store.state.maxFactor).toEqual(1.2);
        expect(store.state.computedBidMin).toEqual('$0.8800');
        expect(store.state.computedBidMax).toEqual('$1.3200');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the target bid CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.8800 - $1.3200');
    });

    it('should correctly update bid range after a change', () => {
        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );
        store.updateSelectedGridRows(store.state.bidModifierTypeGridRows);
        expect(store.state.finalBidRangeValue).toEqual('$0.8800 - $1.3200');

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            '-10.00',
            agencyUsesRealtimeAutopilot
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.7200 - $1.0800');
    });

    it('should correctly present bid range info for CPC / device / active autopilot / selected all dimensions', () => {
        adGroupAutopilotState = AdGroupAutopilotState.ACTIVE_CPC_BUDGET;

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );
        store.updateSelectedGridRows(store.state.bidModifierTypeGridRows);

        expect(store.state.bidModifierTypeSummaries).toEqual([]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual({
            type: BidModifierType.SOURCE,
            count: 4,
            min: 0.8,
            max: 1.2,
        } as BidModifierTypeSummary);
        expect(store.state.autopilot).toEqual(true);
        expect(store.state.minFactor).toEqual(1);
        expect(store.state.maxFactor).toEqual(1);
        expect(store.state.computedBidMin).toEqual('$0.0001');
        expect(store.state.computedBidMax).toEqual('$1.3200');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the autopilot’s bid CPC and modifiers applied by you on all dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Autopilot bid CPC range:');
        expect(store.state.formattedBidValueRange).toEqual('$0.0001 - $1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.0001 - $1.3200');
    });

    it('should correctly present bid range info for CPC / source / active autopilot / selected all dimensions', () => {
        bidModifier = {
            type: BidModifierType.SOURCE,
            target: 'example.com',
            modifier: 0.9,
        } as BidModifier;
        adGroupAutopilotState = AdGroupAutopilotState.ACTIVE_CPC_BUDGET;

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );
        store.updateSelectedGridRows(store.state.bidModifierTypeGridRows);

        expect(store.state.bidModifierTypeSummaries).toEqual([
            {
                type: BidModifierType.DEVICE,
                count: 2,
                min: 0.9,
                max: 1.1,
            } as BidModifierTypeSummary,
        ]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual({
            type: BidModifierType.SOURCE,
            count: 4,
            min: 0.8,
            max: 1.2,
        } as BidModifierTypeSummary);
        expect(store.state.autopilot).toEqual(true);
        expect(store.state.minFactor).toEqual(0.9);
        expect(store.state.maxFactor).toEqual(1.1);
        expect(store.state.computedBidMin).toEqual('$0.0001');
        expect(store.state.computedBidMax).toEqual('$0.9900');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the autopilot’s bid CPC and modifiers applied by you on all dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Autopilot bid CPC range:');
        expect(store.state.formattedBidValueRange).toEqual('$0.0001 - $1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.0001 - $0.9900');
    });

    it('should correctly present bid range info for CPC / no source bid modifier / active autopilot / selected all dimensions', () => {
        bidModifier = {
            type: BidModifierType.SOURCE,
            target: 'example.com',
            modifier: null,
        } as BidModifier;
        bidModifierTypeSummaries = [] as BidModifierTypeSummary[];
        adGroupAutopilotState = AdGroupAutopilotState.ACTIVE_CPC_BUDGET;

        store.updateInputs(
            bidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries,
            currency,
            fractionSize,
            adGroupAutopilotState,
            modifierPercent,
            agencyUsesRealtimeAutopilot
        );
        store.updateSelectedGridRows(store.state.bidModifierTypeGridRows);

        expect(store.state.bidModifierTypeSummaries).toEqual([]);
        expect(store.state.sourceBidModifierTypeSummary).toEqual(null);
        expect(store.state.autopilot).toEqual(true);
        expect(store.state.minFactor).toEqual(1.0);
        expect(store.state.maxFactor).toEqual(1.0);
        expect(store.state.computedBidMin).toEqual('$0.0001');
        expect(store.state.computedBidMax).toEqual('$1.0000');
        expect(store.state.infoMessage).toEqual(
            'Your final bid CPC is determined by the autopilot’s bid CPC and modifiers applied by you on all dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final bid CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Autopilot bid CPC range:');
        expect(store.state.formattedBidValueRange).toEqual('$0.0001 - $1.0000');
        expect(store.state.finalBidRangeMessage).toEqual(
            'Final bid CPC range:'
        );
        expect(store.state.finalBidRangeValue).toEqual('$0.0001 - $1.0000');
    });
});
