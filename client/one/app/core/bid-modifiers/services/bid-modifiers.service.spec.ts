import {BidModifiersService} from './bid-modifiers.service';
import {BidModifiersEndpoint} from './bid-modifiers.endpoint';
import {of} from 'rxjs';
import {BidModifierType, Breakdown} from '../../../app.constants';
import {BidModifier} from '../types/bid-modifier';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as clone from 'clone';

describe('BidModifiersService', () => {
    let service: BidModifiersService;
    let endpointStub: jasmine.SpyObj<BidModifiersEndpoint>;
    let mocketAdGroupId: number;
    let mockedBidModifier: BidModifier;
    let mockedBreakdown: Breakdown;
    let mockedFile: File;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        endpointStub = jasmine.createSpyObj(BidModifiersEndpoint.name, [
            'create',
            'edit',
            'upload',
        ]);
        service = new BidModifiersService(endpointStub);
        mocketAdGroupId = 1234;
        mockedBidModifier = {
            id: null,
            type: BidModifierType.DEVICE,
            sourceSlug: 'Slug 1',
            target: 'http://www.target.com',
            bidMin: '0.20',
            bidMax: '0.21',
            modifier: 1,
        };
        mockedBreakdown = Breakdown.DEVICE;
        mockedFile = null;
        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should correctly create bid modifier for adGroup', () => {
        const createBidModifier = clone(mockedBidModifier);
        createBidModifier.id = 1234;

        endpointStub.create.and
            .returnValue(of(createBidModifier))
            .calls.reset();

        service
            .save(mocketAdGroupId, mockedBidModifier, requestStateUpdater)
            .subscribe(response => {
                expect(response).toEqual(createBidModifier);
            });

        expect(endpointStub.create).toHaveBeenCalledTimes(1);
        expect(endpointStub.create).toHaveBeenCalledWith(
            mocketAdGroupId,
            mockedBidModifier,
            requestStateUpdater
        );
        expect(endpointStub.edit).not.toHaveBeenCalled();
    });

    it('should correctly edit bid modifier for adGroup', () => {
        const editBidModifier = clone(mockedBidModifier);
        editBidModifier.id = 1234;

        endpointStub.edit.and.returnValue(of(editBidModifier)).calls.reset();

        service
            .save(mocketAdGroupId, editBidModifier, requestStateUpdater)
            .subscribe(response => {
                expect(response).toEqual(editBidModifier);
            });

        expect(endpointStub.edit).toHaveBeenCalledTimes(1);
        expect(endpointStub.edit).toHaveBeenCalledWith(
            mocketAdGroupId,
            editBidModifier,
            requestStateUpdater
        );
        expect(endpointStub.create).not.toHaveBeenCalled();
    });

    it('should correctly import bid modifiers from file', () => {
        endpointStub.upload.and.returnValue(of()).calls.reset();

        service
            .importFromFile(
                mocketAdGroupId,
                mockedBreakdown,
                mockedFile,
                requestStateUpdater
            )
            .subscribe();

        expect(endpointStub.upload).toHaveBeenCalledTimes(1);
        expect(endpointStub.upload).toHaveBeenCalledWith(
            mocketAdGroupId,
            mockedBreakdown,
            mockedFile,
            requestStateUpdater
        );
    });
});
