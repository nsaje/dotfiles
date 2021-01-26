import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {
    ValidateCreativeBatchAction,
    ValidateCreativeBatchActionEffect,
} from './validate-creative-batch.effect';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStatus} from '../../../../../../core/creatives/types/creative-batch-status';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, throwError} from 'rxjs';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeBatchStoreFieldsErrorsState} from '../creative-batch.store.fields-errors-state';
import {SetFieldsErrorsAction} from '../reducers/set-fields-errors.reducer';

describe('ValidateCreativeBatchActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: ValidateCreativeBatchActionEffect = new ValidateCreativeBatchActionEffect(
        creativesServiceStub
    );
    let mockedBatch: CreativeBatch;
    let mockedState: CreativeBatchStoreState;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'validateBatch',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new ValidateCreativeBatchActionEffect(creativesServiceStub);
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

        mockedState = {
            ...new CreativeBatchStoreState(),
            entity: mockedBatch,
        };
    });

    it('should validate creative batch via service - valid', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.validateBatch.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        effect.effect(
            mockedState,
            new ValidateCreativeBatchAction({
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.validateBatch).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.validateBatch).toHaveBeenCalledWith(
            mockedBatch,
            requestStateUpdater
        );
        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetFieldsErrorsAction(new CreativeBatchStoreFieldsErrorsState())
        );
    }));

    it('should validate creative batch via service - invalid', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.validateBatch.and
            .returnValue(
                throwError({
                    status: 400,
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify batch name.']},
                    },
                })
            )
            .calls.reset();

        effect.effect(
            mockedState,
            new ValidateCreativeBatchAction({
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.validateBatch).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.validateBatch).toHaveBeenCalledWith(
            mockedBatch,
            requestStateUpdater
        );
        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetFieldsErrorsAction({
                ...new CreativeBatchStoreFieldsErrorsState(),
                name: ['Please specify batch name.'],
            })
        );
    }));
});
