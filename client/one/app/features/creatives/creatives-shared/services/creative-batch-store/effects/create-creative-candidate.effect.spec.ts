import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {
    CreateCreativeCandidateAction,
    CreateCreativeCandidateActionEffect,
} from './create-creative-candidate.effect';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';

describe('CreateCreativeCandidateActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: CreateCreativeCandidateActionEffect;
    const mockedBatchId = '123';
    const mockedCandidate1: CreativeCandidate = {
        id: '1',
        title: 'Test candidate 1',
    };
    const mockedCandidate2: CreativeCandidate = {
        id: '2',
        title: 'Test candidate 2',
    };

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'createCandidate',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new CreateCreativeCandidateActionEffect(creativesServiceStub);
    });

    it('should create creative candidate via service', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.createCandidate.and
            .returnValue(of(mockedCandidate2, asapScheduler))
            .calls.reset();

        const mockedStoreState: CreativeBatchStoreState = new CreativeBatchStoreState();
        mockedStoreState.entity.id = mockedBatchId;
        mockedStoreState.candidates = [mockedCandidate1];

        effect.effect(
            mockedStoreState,
            new CreateCreativeCandidateAction({
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.createCandidate).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.createCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            {},
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction([mockedCandidate1, mockedCandidate2])
        );
    }));
});
