import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {
    FetchCreativeBatchAction,
    FetchCreativeBatchActionEffect,
} from './fetch-creative-batch.effect';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStatus} from '../../../../../../core/creatives/types/creative-batch-status';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetEntityAction} from '../reducers/set-entity.reducer';

describe('FetchCreativeBatchActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: FetchCreativeBatchActionEffect = new FetchCreativeBatchActionEffect(
        creativesServiceStub
    );
    let mockedBatch: CreativeBatch;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'getBatch',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCreativeBatchActionEffect(creativesServiceStub);
        mockedBatch = {
            id: '1',
            agencyId: '2',
            accountId: null,
            name: 'test',
            status: CreativeBatchStatus.IN_PROGRESS,
            tags: [],
            imageCrop: null,
            displayUrl: null,
            brandName: null,
            description: null,
            callToAction: null,
            createdBy: null,
            createdDt: null,
        };
    });

    it('should fetch creative batch via service', fakeAsync(() => {
        const batchId: string = mockedBatch.id;

        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.getBatch.and
            .returnValue(of(mockedBatch, asapScheduler))
            .calls.reset();

        effect.effect(
            new CreativeBatchStoreState(),
            new FetchCreativeBatchAction({
                batchId,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.getBatch).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.getBatch).toHaveBeenCalledWith(
            batchId,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetEntityAction(mockedBatch)
        );
    }));
});
