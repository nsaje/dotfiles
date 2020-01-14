import {BidRangeInfoStore} from './bid-range-info.store';
import {
    BidModifierType,
    BiddingType,
    Currency,
    AdGroupAutopilotState,
} from '../../../../../../app.constants';
import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import {BidModifierTypeSummary} from '../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';

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
        fractionSize = 2;
        adGroupAutopilotState = AdGroupAutopilotState.INACTIVE;
        modifierPercent = null;
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
            modifierPercent
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$1.10');
        expect(store.state.computedBidMax).toEqual('$1.10');
        expect(store.state.infoMessage).toEqual(
            'Your final CPC depends on target CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.00');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPC range:');
        expect(store.state.finalBidRangeValue).toEqual('$1.10 to $1.10');
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$1.10');
        expect(store.state.computedBidMax).toEqual('$1.10');
        expect(store.state.infoMessage).toEqual(
            'Your final CPM depends on target CPM set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPM range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPM:');
        expect(store.state.formattedBidValueRange).toEqual('$1.00');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPM range:');
        expect(store.state.finalBidRangeValue).toEqual('$1.10 to $1.10');
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$0.90');
        expect(store.state.computedBidMax).toEqual('$0.90');
        expect(store.state.infoMessage).toEqual(
            'Your final CPC depends on target CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.00');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPC range:');
        expect(store.state.finalBidRangeValue).toEqual('$0.90 to $0.90');
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$0.88');
        expect(store.state.computedBidMax).toEqual('$1.32');
        expect(store.state.infoMessage).toEqual(
            'Your final CPC depends on target CPC set in the ad group settings and bid modifiers you set on this and other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Bid CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$1.00');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPC range:');
        expect(store.state.finalBidRangeValue).toEqual('$0.88 to $1.32');
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$0.88');
        expect(store.state.computedBidMax).toEqual('$1.32');
        expect(store.state.infoMessage).toEqual(
            'Your final CPC depends on CPC set by the autopilot on media source and bid modifiers set by you on other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPC range.'
        );
        expect(store.state.bidMessage).toEqual(
            'Autopilot media source CPC range:'
        );
        expect(store.state.formattedBidValueRange).toEqual('$0.80 to $1.20');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPC range:');
        expect(store.state.finalBidRangeValue).toEqual('$0.88 to $1.32');
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
            modifierPercent
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
        expect(store.state.computedBidMin).toEqual('$0.81');
        expect(store.state.computedBidMax).toEqual('$0.99');
        expect(store.state.infoMessage).toEqual(
            'Your final CPC depends on CPC set by the autopilot on media source and bid modifiers set by you on other dimensions.'
        );
        expect(store.state.selectionTooltipMessage).toEqual(
            'Dimensions that you select will be included in the calculation of final CPC range.'
        );
        expect(store.state.bidMessage).toEqual('Autopilot media source CPC:');
        expect(store.state.formattedBidValueRange).toEqual('$0.90');
        expect(store.state.finalBidRangeMessage).toEqual('Final CPC range:');
        expect(store.state.finalBidRangeValue).toEqual('$0.81 to $0.99');
    });
});
