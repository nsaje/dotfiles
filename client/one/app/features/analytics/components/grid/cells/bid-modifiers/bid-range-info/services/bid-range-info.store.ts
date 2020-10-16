import {Injectable} from '@angular/core';
import {BidRangeInfoStoreState} from './bid-range-info.store.state';
import {Store} from 'rxjs-observable-store';
import {BidModifier} from '../../../../../../../../core/bid-modifiers/types/bid-modifier';
import * as clone from 'clone';
import * as commonHelpers from '../../../../../../../../shared/helpers/common.helpers';
import * as currencyHelpers from '../../../../../../../../shared/helpers/currency.helpers';
import {
    Currency,
    BiddingType,
    BidModifierType,
    AdGroupAutopilotState,
} from '../../../../../../../../app.constants';
import {TypeSummaryGridRow} from '../../../../../../../../shared/components/bid-modifier-types-grid/services/type-summary-grid-row';
import {BidModifierTypeSummary} from '../../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {convertToTypeSummaryGridRows} from '../../../../../../../../core/bid-modifiers/bid-modifiers.helpers';
import {isDefined} from '../../../../../../../../shared/helpers/common.helpers';

@Injectable()
export class BidRangeInfoStore extends Store<BidRangeInfoStoreState> {
    constructor() {
        super(new BidRangeInfoStoreState());
    }

    updateInputs(
        bidModifier: BidModifier,
        biddingType: BiddingType,
        bid: string,
        bidModifierTypeSummaries: BidModifierTypeSummary[],
        currency: Currency,
        fractionSize: number,
        adGroupAutopilotState: AdGroupAutopilotState,
        modifierPercent: string,
        agencyUsesRealtimeAutopilot: boolean
    ): void {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.updateInputsLegacy(
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
        }

        const summariesWithoutCurrentType: BidModifierTypeSummary[] = bidModifierTypeSummaries.filter(
            summary => summary.type !== bidModifier.type
        );

        const newBidModifier: BidModifier = {
            ...bidModifier,
            modifier: bidModifier.modifier ?? 1.0,
        };

        if (isDefined(modifierPercent)) {
            newBidModifier.modifier = this.convertPercentToModifier(
                parseFloat(modifierPercent)
            );
        }

        this.setState({
            ...this.state,
            bidModifier: newBidModifier,
            biddingType,
            bid,
            bidModifierTypeSummaries: summariesWithoutCurrentType,
            sourceBidModifierTypeSummary: null,
            bidModifierTypeGridRows: convertToTypeSummaryGridRows(
                summariesWithoutCurrentType
            ),
            currency,
            fractionSize,
            adGroupAutopilotState,
            autopilot: adGroupAutopilotState !== AdGroupAutopilotState.INACTIVE,
            minFactor: this.state.minFactor ?? 1.0,
            maxFactor: this.state.maxFactor ?? 1.0,
            agencyUsesRealtimeAutopilot,
        });

        this.updateInfo();
        this.updateComputedBidMinMax();
    }

    updateSelectedGridRows(gridRows: TypeSummaryGridRow[]) {
        let minFactor = 1.0;
        let maxFactor = 1.0;

        gridRows.forEach(gridRow => {
            minFactor *= gridRow.limits.min;
            maxFactor *= gridRow.limits.max;
        });

        this.setState({
            ...this.state,
            minFactor: minFactor,
            maxFactor: maxFactor,
        });

        this.updateComputedBidMinMax();
    }

    private updateInfo(): void {
        this.setState({
            ...this.state,
            infoMessage: this.composeInfoMessage(),
            selectionTooltipMessage: this.composeSelectionTooltipMessage(),
            finalBidRangeMessage: this.composeFinalBidRangeMessage(),
            bidMessage: this.composeBidMessage(),
            formattedBidValueRange: this.composeFormattedBidValueRange(),
        });
    }

    private updateComputedBidMinMax(): void {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.updateComputedBidMinMaxLegacy();
        }

        if (
            !(
                commonHelpers.isDefined(this.state.bid) &&
                commonHelpers.isDefined(this.state.currency) &&
                commonHelpers.isDefined(this.state.fractionSize) &&
                commonHelpers.isDefined(this.state.minFactor) &&
                commonHelpers.isDefined(this.state.maxFactor)
            )
        ) {
            return;
        }

        const limits:
            | {min: string; max: string}
            | undefined = this.computeBidMinMax();

        const finalBidRangeValue: string | null = isDefined(limits)
            ? limits.min + ' - ' + limits.max
            : null;

        this.setState({
            ...this.state,
            computedBidMin: limits.min,
            computedBidMax: limits.max,
            finalBidRangeValue: finalBidRangeValue,
        });
    }

    private computeBidMinMax(): {min: string; max: string} | undefined {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.computeBidMinMaxLegacy();
        }

        let minFactor: number = this.state.bidModifier.modifier
            ? this.state.bidModifier.modifier
            : 1.0;
        let maxFactor: number = this.state.bidModifier.modifier
            ? this.state.bidModifier.modifier
            : 1.0;

        if (
            commonHelpers.isDefined(this.state.autopilot) &&
            this.state.autopilot &&
            commonHelpers.isDefined(this.state.sourceBidModifierTypeSummary) &&
            this.state.bidModifier.type !== BidModifierType.SOURCE
        ) {
            // in autopilot mode source dimension is implicitly included in calculation
            minFactor *= this.state.sourceBidModifierTypeSummary.min;
            maxFactor *= this.state.sourceBidModifierTypeSummary.max;
        }

        minFactor *= this.state.minFactor;
        maxFactor *= this.state.maxFactor;

        const numericBid: number = Number.parseFloat(this.state.bid);

        const minPercent: number = this.convertModifierToPercent(minFactor);
        const maxPercent: number = this.convertModifierToPercent(maxFactor);

        let minBid: number = this.getBid(minPercent, numericBid);
        const maxBid: number = this.getBid(maxPercent, numericBid);

        if (this.state.autopilot && !isDefined(maxBid)) {
            return undefined;
        }
        if (this.state.autopilot) {
            minBid = 0.0001;
        }

        const computedBidMin = this.formatBid(
            minBid,
            this.state.fractionSize,
            this.state.currency
        );
        const computedBidMax = this.formatBid(
            maxBid,
            this.state.fractionSize,
            this.state.currency
        );

        return {min: computedBidMin, max: computedBidMax};
    }

    private convertModifierToPercent(modifier: number): number {
        return !commonHelpers.isDefined(modifier) || isNaN(modifier)
            ? 0.0
            : modifier * 100 - 100;
    }

    private convertPercentToModifier(modifierPercent: number): number {
        return !commonHelpers.isDefined(modifierPercent) ||
            isNaN(modifierPercent)
            ? 0.0
            : (modifierPercent + 100) / 100.0;
    }

    private getBid(modifierPercent: number, bid: number): number {
        if (!commonHelpers.isDefined(bid) || isNaN(bid)) {
            return 0.0;
        }
        if (
            !commonHelpers.isDefined(modifierPercent) ||
            isNaN(modifierPercent)
        ) {
            return bid;
        }
        return bid * this.convertPercentToModifier(modifierPercent);
    }

    private formatBid(
        bid: number,
        fractionSize: number,
        currency: Currency
    ): string {
        return currencyHelpers.formatCurrency(
            bid.toString(),
            currency,
            fractionSize
        );
    }

    private composeInfoMessage(): string {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.composeInfoMessageLegacy();
        }

        if (
            !(
                commonHelpers.isDefined(this.state.biddingType) &&
                commonHelpers.isDefined(this.state.autopilot)
            )
        ) {
            return;
        }

        let message =
            'Your final bid ' +
            this.state.biddingType +
            ' is determined by the ';

        if (this.state.autopilot) {
            message +=
                'autopilot’s bid ' +
                this.state.biddingType +
                ' and modifiers applied by you on all dimensions.';
        } else {
            message +=
                'target bid ' +
                this.state.biddingType +
                ' set in the ad group settings and bid modifiers you set on this and other dimensions.';
        }

        return message;
    }

    private composeBidMessage(): string {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.composeBidMessageLegacy();
        }

        if (
            !(
                commonHelpers.isDefined(this.state.biddingType) &&
                commonHelpers.isDefined(this.state.autopilot)
            )
        ) {
            return;
        }

        let message = null;
        if (this.state.autopilot) {
            message = 'Autopilot bid ' + this.state.biddingType + ' range';
        } else {
            message = 'Bid ' + this.state.biddingType;
        }

        return message + ':';
    }

    private composeFormattedBidValueRange(): string {
        if (!this.state.agencyUsesRealtimeAutopilot) {
            // TODO: RTAP: remove this after Phase 1
            return this.composeFormattedBidValueRangeLegacy();
        }

        if (!commonHelpers.isDefined(this.state.bid)) {
            return 'No limit';
        }

        if (
            !(
                commonHelpers.isDefined(this.state.currency) &&
                commonHelpers.isDefined(this.state.fractionSize)
            )
        ) {
            return;
        }

        if (this.state.autopilot) {
            const formattedMinBid = this.formatBid(
                0.0001,
                this.state.fractionSize,
                this.state.currency
            );
            const formattedMaxBid = this.formatBid(
                Number.parseFloat(this.state.bid),
                this.state.fractionSize,
                this.state.currency
            );

            return formattedMinBid + ' - ' + formattedMaxBid;
        } else {
            // if autopilot is off, display just the bid value
            return this.formatBid(
                Number.parseFloat(this.state.bid),
                this.state.fractionSize,
                this.state.currency
            );
        }
    }

    private composeFinalBidRangeMessage(): string {
        if (!commonHelpers.isDefined(this.state.biddingType)) {
            return;
        }

        return 'Final bid ' + this.state.biddingType + ' range:';
    }

    private composeSelectionTooltipMessage(): string {
        if (!commonHelpers.isDefined(this.state.biddingType)) {
            return;
        }

        const selectionTooltipMessage =
            'Dimensions that you select will be included in the calculation of final bid ' +
            this.state.biddingType +
            ' range.';

        return selectionTooltipMessage;
    }

    // TODO: RTAP: remove everything below this line this after Phase 1 ///////////////////////////////////

    private composeInfoMessageLegacy(): string {
        if (
            !(
                commonHelpers.isDefined(this.state.biddingType) &&
                commonHelpers.isDefined(this.state.autopilot)
            )
        ) {
            return;
        }

        let message =
            'Your final bid ' + this.state.biddingType + ' depends on ';

        if (this.state.autopilot) {
            message +=
                'bid ' +
                this.state.biddingType +
                ' set by the autopilot on media source and bid modifiers set by you on other dimensions.';
        } else {
            message +=
                'target bid ' +
                this.state.biddingType +
                ' set in the ad group settings and bid modifiers you set on this and other dimensions.';
        }

        return message;
    }

    private updateComputedBidMinMaxLegacy(): void {
        if (
            !(
                commonHelpers.isDefined(this.state.bid) &&
                commonHelpers.isDefined(this.state.currency) &&
                commonHelpers.isDefined(this.state.fractionSize) &&
                commonHelpers.isDefined(this.state.minFactor) &&
                commonHelpers.isDefined(this.state.maxFactor)
            )
        ) {
            return;
        }

        const limits = this.computeBidMinMaxLegacy();

        const finalBidRangeValue = limits.min + ' - ' + limits.max;

        this.setState({
            ...this.state,
            computedBidMin: limits.min,
            computedBidMax: limits.max,
            finalBidRangeValue: finalBidRangeValue,
        });
    }

    private computeBidMinMaxLegacy(): {min: string; max: string} {
        let minFactor = this.state.bidModifier.modifier
            ? this.state.bidModifier.modifier
            : 1.0;
        let maxFactor = this.state.bidModifier.modifier
            ? this.state.bidModifier.modifier
            : 1.0;

        if (
            commonHelpers.isDefined(this.state.autopilot) &&
            this.state.autopilot &&
            commonHelpers.isDefined(this.state.sourceBidModifierTypeSummary) &&
            this.state.bidModifier.type !== BidModifierType.SOURCE
        ) {
            // in autopilot mode source dimension is implicitly included in calculation
            minFactor *= this.state.sourceBidModifierTypeSummary.min;
            maxFactor *= this.state.sourceBidModifierTypeSummary.max;
        }

        minFactor *= this.state.minFactor;
        maxFactor *= this.state.maxFactor;

        const numericBid = Number.parseFloat(this.state.bid);

        const minPercent = this.convertModifierToPercent(minFactor);
        const maxPercent = this.convertModifierToPercent(maxFactor);

        const minBid = this.getBid(minPercent, numericBid);
        const maxBid = this.getBid(maxPercent, numericBid);

        const computedBidMin = this.formatBid(
            minBid,
            this.state.fractionSize,
            this.state.currency
        );
        const computedBidMax = this.formatBid(
            maxBid,
            this.state.fractionSize,
            this.state.currency
        );

        return {min: computedBidMin, max: computedBidMax};
    }

    private composeBidMessageLegacy(): string {
        if (
            !(
                commonHelpers.isDefined(this.state.biddingType) &&
                commonHelpers.isDefined(this.state.autopilot)
            )
        ) {
            return;
        }

        let message = null;
        if (this.state.autopilot) {
            message = 'Autopilot media source bid ' + this.state.biddingType;
            if (this.state.bidModifier.type !== BidModifierType.SOURCE) {
                message += ' range';
            }
        } else {
            message = 'Bid ' + this.state.biddingType;
        }

        return message + ':';
    }

    private composeFormattedBidValueRangeLegacy(): string {
        if (
            !(
                commonHelpers.isDefined(this.state.bid) &&
                commonHelpers.isDefined(this.state.currency) &&
                commonHelpers.isDefined(this.state.fractionSize)
            )
        ) {
            return;
        }

        if (!this.state.autopilot) {
            // if autopilot is off, display just the bid value
            return this.formatBid(
                Number.parseFloat(this.state.bid),
                this.state.fractionSize,
                this.state.currency
            );
        }

        if (
            commonHelpers.isDefined(this.state.bidModifier) &&
            this.state.bidModifier.type === BidModifierType.SOURCE
        ) {
            // for source dimension multiply bid value with current bid modifier
            const bid =
                Number.parseFloat(this.state.bid) *
                this.state.bidModifier.modifier;
            return this.formatBid(
                bid,
                this.state.fractionSize,
                this.state.currency
            );
        }

        // for other dimensions multiply bid value with min & max source bid modifiers
        if (!commonHelpers.isDefined(this.state.sourceBidModifierTypeSummary)) {
            return;
        }

        const bid = Number.parseFloat(this.state.bid);
        const minBid = bid * this.state.sourceBidModifierTypeSummary.min;
        const maxBid = bid * this.state.sourceBidModifierTypeSummary.max;

        const formattedMinBid = this.formatBid(
            minBid,
            this.state.fractionSize,
            this.state.currency
        );
        const formattedMaxBid = this.formatBid(
            maxBid,
            this.state.fractionSize,
            this.state.currency
        );

        return formattedMinBid + ' - ' + formattedMaxBid;
    }

    updateInputsLegacy(
        bidModifier: BidModifier,
        biddingType: BiddingType,
        bid: string,
        bidModifierTypeSummaries: BidModifierTypeSummary[],
        currency: Currency,
        fractionSize: number,
        adGroupAutopilotState: AdGroupAutopilotState,
        modifierPercent: string,
        agencyUsesRealtimeAutopilot: boolean
    ): void {
        const autopilot =
            adGroupAutopilotState === AdGroupAutopilotState.ACTIVE_CPC ||
            adGroupAutopilotState === AdGroupAutopilotState.ACTIVE_CPC_BUDGET;
        const splitSummaries = this.splitTypeSummariesLegacy(
            bidModifierTypeSummaries,
            autopilot,
            bidModifier.type
        );

        const newBidModifier = clone(bidModifier);
        if (!commonHelpers.isDefined(newBidModifier.modifier)) {
            newBidModifier.modifier = 1.0;
        }

        if (commonHelpers.isDefined(modifierPercent)) {
            const newModifierValue = this.convertPercentToModifier(
                parseFloat(modifierPercent)
            );
            newBidModifier.modifier = newModifierValue;
        }

        const minFactor = this.state.minFactor ? this.state.minFactor : 1.0;
        const maxFactor = this.state.maxFactor ? this.state.maxFactor : 1.0;

        const bidModifierTypeGridRows = convertToTypeSummaryGridRows(
            splitSummaries.summaries
        );

        this.setState({
            ...this.state,
            bidModifier: newBidModifier,
            biddingType: biddingType,
            bid: bid,
            bidModifierTypeSummaries: splitSummaries.summaries,
            sourceBidModifierTypeSummary: splitSummaries.sourceSummary,
            bidModifierTypeGridRows: bidModifierTypeGridRows,
            currency: currency,
            fractionSize: fractionSize,
            adGroupAutopilotState: adGroupAutopilotState,
            autopilot: autopilot,
            minFactor: minFactor,
            maxFactor: maxFactor,
            agencyUsesRealtimeAutopilot,
        });

        this.updateInfo();
        this.updateComputedBidMinMax();
    }

    private splitTypeSummariesLegacy(
        inputSummaries: BidModifierTypeSummary[],
        autopilot: boolean,
        bidModifierType: BidModifierType
    ): {
        summaries: BidModifierTypeSummary[];
        sourceSummary: BidModifierTypeSummary;
    } {
        let sourceSummary = null;
        if (autopilot) {
            const res = this.removeTypeSummaryLegacy(
                inputSummaries,
                BidModifierType.SOURCE
            );
            sourceSummary = res.removedSummary;
            inputSummaries = res.summaries;
        }

        const res = this.removeTypeSummaryLegacy(
            inputSummaries,
            bidModifierType
        );
        return {summaries: res.summaries, sourceSummary: sourceSummary};
    }

    private removeTypeSummaryLegacy(
        inputSummaries: BidModifierTypeSummary[],
        bidModifierType: BidModifierType
    ): {
        summaries: BidModifierTypeSummary[];
        removedSummary: BidModifierTypeSummary;
    } {
        if (commonHelpers.isDefined(inputSummaries)) {
            const currentDimIndex = inputSummaries.findIndex(
                element => element.type === bidModifierType
            );
            if (currentDimIndex >= 0) {
                const currentDimSummary = inputSummaries[currentDimIndex];
                const summaries = inputSummaries.slice();
                summaries.splice(currentDimIndex, 1);

                return {
                    summaries: summaries,
                    removedSummary: currentDimSummary,
                };
            }
        }
        return {summaries: inputSummaries, removedSummary: null};
    }
}
