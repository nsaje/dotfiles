import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {
    EditCreativeCandidateAction,
    EditCreativeCandidateActionEffect,
} from './edit-creative-candidate.effect';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';

describe('EditCreativeCandidateActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let requestStateUpdater: RequestStateUpdater;
    let effect: EditCreativeCandidateActionEffect;
    const mockedBatchId = '123';
    const mockedCandidate1: CreativeCandidate = {
        id: '1',
        title: 'Test candidate 1',
    };
    const mockedCandidate2: CreativeCandidate = {
        id: '2',
        title: 'Test candidate 2',
    };
    const mockedChanges: Partial<CreativeCandidate> = {
        title: 'This is the new test candidate 2',
    };
    const mockedNewCandidate2: CreativeCandidate = {
        ...mockedCandidate2,
        ...mockedChanges,
    };
    const mockedNewCandidate2FromServer: CreativeCandidate = {
        id: '2',
        title: 'This is the new test candidate 2 returned from the server',
    };

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'editCandidate',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new EditCreativeCandidateActionEffect(creativesServiceStub);
    });

    it('should edit creative candidate via service', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.editCandidate.and
            .returnValue(of(mockedNewCandidate2FromServer, asapScheduler))
            .calls.reset();

        const mockedStoreState: CreativeBatchStoreState = new CreativeBatchStoreState();
        mockedStoreState.entity.id = mockedBatchId;
        mockedStoreState.candidates = [mockedCandidate1, mockedCandidate2];

        effect.effect(
            mockedStoreState,
            new EditCreativeCandidateAction({
                candidate: mockedCandidate2,
                changes: mockedChanges,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.editCandidate).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.editCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCandidate2.id,
            {
                ...mockedChanges,
                type: mockedNewCandidate2.type,
            },
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction([
                mockedCandidate1,
                mockedNewCandidate2FromServer,
            ])
        );
    }));
});
