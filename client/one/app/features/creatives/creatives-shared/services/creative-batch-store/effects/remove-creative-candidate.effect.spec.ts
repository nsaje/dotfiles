import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {
    RemoveCreativeCandidateAction,
    RemoveCreativeCandidateActionEffect,
} from './remove-creative-candidate.effect';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {SetSelectedCandidateAction} from '../reducers/set-selected-candidate.reducer';

describe('RemoveCreativeCandidateActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: RemoveCreativeCandidateActionEffect;
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
            'removeCandidate',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new RemoveCreativeCandidateActionEffect(creativesServiceStub);
    });

    it('should remove creative candidate via service', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.removeCandidate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        const mockedStoreState: CreativeBatchStoreState = new CreativeBatchStoreState();
        mockedStoreState.entity.id = mockedBatchId;
        mockedStoreState.candidates = [mockedCandidate1, mockedCandidate2];
        mockedStoreState.selectedCandidateId = mockedCandidate1.id;

        effect.effect(
            mockedStoreState,
            new RemoveCreativeCandidateAction({
                candidate: mockedCandidate2,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.removeCandidate).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.removeCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCandidate2.id,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction([mockedCandidate1])
        );
    }));

    it('should deselect candidate after removal if it was selected', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.removeCandidate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        const mockedStoreState: CreativeBatchStoreState = new CreativeBatchStoreState();
        mockedStoreState.entity.id = mockedBatchId;
        mockedStoreState.candidates = [mockedCandidate1, mockedCandidate2];
        mockedStoreState.selectedCandidateId = mockedCandidate2.id; // This ID is the difference from the previous test

        effect.effect(
            mockedStoreState,
            new RemoveCreativeCandidateAction({
                candidate: mockedCandidate2,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.removeCandidate).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.removeCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCandidate2.id,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(2);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction([mockedCandidate1])
        );
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetSelectedCandidateAction(undefined)
        );
    }));
});
