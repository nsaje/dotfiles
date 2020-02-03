import {OnDestroy, Injectable} from '@angular/core';
import {BidModifierCellStoreState} from './bid-modifier-cell.store.state';
import {Store} from 'rxjs-observable-store';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {BidModifiersService} from '../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import * as storeHelpers from '../../../../../../shared/helpers/store.helpers';
import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import * as clone from 'clone';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {Currency} from '../../../../../../app.constants';

@Injectable()
export class BidModifierCellStore extends Store<BidModifierCellStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private bidModifierService: BidModifiersService) {
        super(new BidModifierCellStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadBidModifier(
        bidModifier: BidModifier,
        adGroupId: number,
        currency: Currency
    ): void {
        const modifierPercent = this.convertModifierToPercent(
            bidModifier.modifier
        ).toFixed(this.state.fractionSize);

        this.setState({
            ...this.state,
            adGroupId: adGroupId,
            value: clone(bidModifier),
            currency: currency,
            modifierPercent: modifierPercent,
            previousModifierPercent: modifierPercent,
        });
    }

    updateBidModifier($event: string): void {
        this.patchState($event, 'modifierPercent');
    }

    saveBidModifier(): Promise<any> {
        const adGroupId = this.state.adGroupId;
        const value = clone(this.state.value);
        value.modifier = this.convertPercentToModifier(
            parseFloat(this.state.modifierPercent)
        );

        return new Promise<any>((resolve, reject) => {
            this.bidModifierService
                .save(adGroupId, value, this.requestStateUpdater)
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
}
