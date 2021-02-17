import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {
    CreateCreativeBatchAction,
    CreateCreativeBatchActionEffect,
} from './create-creative-batch.effect';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStatus} from '../../../../../../core/creatives/types/creative-batch-status';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetEntityAction} from '../reducers/set-entity.reducer';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {
    CreativeBatchMode,
    CreativeBatchType,
} from '../../../../../../app.constants';

describe('CreateCreativeBatchActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: CreateCreativeBatchActionEffect = new CreateCreativeBatchActionEffect(
        creativesServiceStub
    );
    let mockedBatch: CreativeBatch;
    let mockedScope: ScopeParams;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'createBatch',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new CreateCreativeBatchActionEffect(creativesServiceStub);
        mockedBatch = {
            id: '1',
            agencyId: '2',
            accountId: null,
            type: CreativeBatchType.NATIVE,
            mode: CreativeBatchMode.INSERT,
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
        mockedScope = {
            agencyId: '2',
            accountId: null,
        };
    });

    it('should create creative batch via service', fakeAsync(() => {
        const batchId: string = mockedBatch.id;

        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.createBatch.and
            .returnValue(of(mockedBatch, asapScheduler))
            .calls.reset();

        effect.effect(
            new CreativeBatchStoreState(),
            new CreateCreativeBatchAction({
                scope: mockedScope,
                type: CreativeBatchType.NATIVE,
                mode: CreativeBatchMode.INSERT,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.createBatch).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.createBatch).toHaveBeenCalledWith(
            {
                agencyId: mockedScope.agencyId,
                accountId: mockedScope.accountId,
                type: CreativeBatchType.NATIVE,
                mode: CreativeBatchMode.INSERT,
            },
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetEntityAction(mockedBatch)
        );
    }));
});
