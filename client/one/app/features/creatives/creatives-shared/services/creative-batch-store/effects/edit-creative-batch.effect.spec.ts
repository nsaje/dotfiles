import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {
    EditCreativeBatchAction,
    EditCreativeBatchActionEffect,
} from './edit-creative-batch.effect';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStatus} from '../../../../../../core/creatives/types/creative-batch-status';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetEntityAction} from '../reducers/set-entity.reducer';
import {ScopeParams} from '../../../../../../shared/types/scope-params';

describe('EditCreativeBatchActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: EditCreativeBatchActionEffect = new EditCreativeBatchActionEffect(
        creativesServiceStub
    );
    let mockedBatch: CreativeBatch;
    let mockedBatchFromBackend: CreativeBatch;
    let mockedScope: ScopeParams;
    let mockedState: CreativeBatchStoreState;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'editBatch',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new EditCreativeBatchActionEffect(creativesServiceStub);
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
        mockedBatchFromBackend = {
            ...mockedBatch,
            name: 'test 2',
        };
        mockedScope = {
            agencyId: '2',
            accountId: null,
        };
    });

    it('should edit creative batch via service', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.editBatch.and
            .returnValue(of(mockedBatchFromBackend, asapScheduler))
            .calls.reset();

        mockedState = {
            ...new CreativeBatchStoreState(),
            entity: mockedBatch,
        };

        effect.effect(
            mockedState,
            new EditCreativeBatchAction({
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.editBatch).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.editBatch).toHaveBeenCalledWith(
            mockedBatch,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetEntityAction(mockedBatchFromBackend)
        );
    }));
});
