import {BidModifierUpdateAction, BidModifierType} from '../../../app.constants';
import {BidModifierUpdatesService} from './bid-modifier-updates.service';
import {BidModifierUpdate} from '../types/bid-modifier-update';

describe('BidModifierUpdatesService', () => {
    let service: BidModifierUpdatesService;
    let mockedBidModifierUpdate: BidModifierUpdate;

    beforeEach(() => {
        mockedBidModifierUpdate = {
            adGroupId: 1,
            bidModifier: {
                id: 1,
                type: BidModifierType.AD,
                target: 'x',
                modifier: 1,
            },
            action: BidModifierUpdateAction.EDIT,
        };

        service = new BidModifierUpdatesService();
    });

    it('should notify subscribers about bid modifier update when bid modifier update is registered', () => {
        service.getAllUpdates$().subscribe(bidModifierUpdate => {
            expect(bidModifierUpdate).toEqual(mockedBidModifierUpdate);
        });

        service.registerBidModifierUpdate(mockedBidModifierUpdate);
    });
});
