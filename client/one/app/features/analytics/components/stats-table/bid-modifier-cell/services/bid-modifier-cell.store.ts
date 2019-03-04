import {OnDestroy, Injectable} from '@angular/core';
import {BidModifierCellStoreState} from './bid-modifier-cell.store.state';
import {Store} from 'rxjs-observable-store';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {BidModifiersService} from '../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import * as endpointHelpers from '../../../../../../shared/helpers/endpoint.helpers';
import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import * as clone from 'clone';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import * as currencyHelpers from '../../../../../../shared/helpers/currency.helpers';
import {BID_MODIFIER_CELL_CONFIG} from '../bid-modifier-cell.config';

@Injectable()
export class BidModifierCellStore extends Store<BidModifierCellStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private bidModifierService: BidModifiersService) {
        super(new BidModifierCellStoreState());
        this.requestStateUpdater = endpointHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadBidModifier(
        bidModifier: BidModifier,
        adGroupId: number,
        currency: string
    ): void {
        const modifierPercent = this.convertModifierToPercent(
            bidModifier.modifier
        ).toFixed(BID_MODIFIER_CELL_CONFIG.fractionSize);

        const computedBidMin = this.formatBid(
            this.getBid(
                parseFloat(modifierPercent),
                parseFloat(bidModifier.bidMin)
            ),
            BID_MODIFIER_CELL_CONFIG.fractionSize,
            currency
        );

        const computedBidMax = this.formatBid(
            this.getBid(
                parseFloat(modifierPercent),
                parseFloat(bidModifier.bidMax)
            ),
            BID_MODIFIER_CELL_CONFIG.fractionSize,
            currency
        );

        this.setState({
            ...this.state,
            adGroupId: adGroupId,
            value: clone(bidModifier),
            currency: currency,
            modifierPercent: modifierPercent,
            previousModifierPercent: modifierPercent,
            computedBidMin: computedBidMin,
            computedBidMax: computedBidMax,
        });
    }

    updateBidModifier($event: string): void {
        const computedBidMin = this.formatBid(
            this.getBid(
                parseFloat($event),
                parseFloat(this.state.value.bidMin)
            ),
            BID_MODIFIER_CELL_CONFIG.fractionSize,
            this.state.currency
        );

        const computedBidMax = this.formatBid(
            this.getBid(
                parseFloat($event),
                parseFloat(this.state.value.bidMax)
            ),
            BID_MODIFIER_CELL_CONFIG.fractionSize,
            this.state.currency
        );

        this.setState({
            ...this.state,
            modifierPercent: $event,
            computedBidMin: computedBidMin,
            computedBidMax: computedBidMax,
        });
    }

    saveBidModifier(): Promise<any> {
        const adGroupId = this.state.adGroupId;
        const value = clone(this.state.value);
        value.modifier = this.convertPercentToModifier(
            parseFloat(this.state.modifierPercent)
        );

        return new Promise<any>((resolve, reject) => {
            this.bidModifierService
                .saveModifier(adGroupId, value, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    response => {
                        resolve(response);
                    },
                    error => {
                        reject(error);
                    }
                );
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
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
        if (!commonHelpers.isDefined(bid) && isNaN(bid)) {
            return 0.0;
        }
        if (
            !commonHelpers.isDefined(modifierPercent) &&
            isNaN(modifierPercent)
        ) {
            return bid;
        }
        return bid * this.convertPercentToModifier(modifierPercent);
    }

    private formatBid(
        bid: number,
        fractionSize: number,
        currency: string
    ): string {
        return currencyHelpers.formatCurrency(
            bid.toString(),
            fractionSize,
            'en-US',
            currencyHelpers.getCurrencySymbol(currency)
        );
    }
}
