import {BidModifiersService} from '../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierCellStore} from './bid-modifier-cell.store';
import {
    BidModifierType,
    CURRENCY,
    CURRENCY_SYMBOL,
} from '../../../../../../app.constants';
import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import {of, asapScheduler} from 'rxjs';
import * as clone from 'clone';
import {fakeAsync, tick} from '@angular/core/testing';

describe('BidModifierCellStore', () => {
    let serviceStub: jasmine.SpyObj<BidModifiersService>;
    let store: BidModifierCellStore;
    let mockedAdGroupId: number;
    let mockedBidModifier: BidModifier;
    let mockedCurrency: string;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(BidModifiersService.name, ['save']);
        store = new BidModifierCellStore(serviceStub);
        mockedAdGroupId = 1234;
        mockedBidModifier = {
            id: 1234,
            type: BidModifierType.DEVICE,
            sourceSlug: 'SLUG 1',
            target: 'http://www.target.com',
            bidMin: '0.20',
            bidMax: '0.25',
            modifier: 1,
        };
        mockedCurrency = CURRENCY.USD;
    });

    it('should be correctly initialized', () => {
        store.loadBidModifier(
            mockedBidModifier,
            mockedAdGroupId,
            mockedCurrency
        );
        expect(store.state.adGroupId).toEqual(mockedAdGroupId);
        expect(store.state.value).toEqual(mockedBidModifier);
        expect(store.state.modifierPercent).toEqual('0.00');
        expect(store.state.previousModifierPercent).toEqual('0.00');
        expect(store.state.computedBidMin).toEqual(
            `${CURRENCY_SYMBOL[mockedCurrency]}0.20`
        );
        expect(store.state.computedBidMax).toEqual(
            `${CURRENCY_SYMBOL[mockedCurrency]}0.25`
        );
    });

    it('should correctly update modifier', () => {
        store.loadBidModifier(
            mockedBidModifier,
            mockedAdGroupId,
            mockedCurrency
        );
        store.updateBidModifier('700.00');
        expect(store.state.modifierPercent).toEqual('700.00');
        expect(store.state.previousModifierPercent).toEqual('0.00');
        expect(store.state.computedBidMin).toEqual(
            `${CURRENCY_SYMBOL[mockedCurrency]}1.60`
        );
        expect(store.state.computedBidMax).toEqual(
            `${CURRENCY_SYMBOL[mockedCurrency]}2.00`
        );
    });

    it('should correctly save modifier', fakeAsync(() => {
        store.loadBidModifier(
            mockedBidModifier,
            mockedAdGroupId,
            mockedCurrency
        );

        const editBidModifier = clone(mockedBidModifier);
        editBidModifier.modifier = 8;

        serviceStub.save.and
            .returnValue(of(editBidModifier, asapScheduler))
            .calls.reset();

        store.updateBidModifier('700.00');
        store.saveBidModifier();
        tick();

        expect(serviceStub.save).toHaveBeenCalledTimes(1);
        expect(serviceStub.save).toHaveBeenCalledWith(
            mockedAdGroupId,
            editBidModifier,
            jasmine.any(Function)
        );
    }));
});
