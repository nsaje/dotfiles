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
import {SetCandidateErrorsAction} from '../reducers/set-candidate-errors.reducer';
import {CreativeCandidateFieldsErrorsState} from '../../../types/creative-candidate-fields-errors-state';
import {AdSize} from '../../../../../../app.constants';

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

    const mockedSizeOnBackend: Partial<CreativeCandidate> = {
        imageWidth: 300,
        imageHeight: 600,
    };
    const mockedSizeOnFrontend: Partial<CreativeCandidate> = {
        size: AdSize.HALF_PAGE,
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

        expect(effect.dispatch).toHaveBeenCalledTimes(2);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction([
                mockedCandidate1,
                mockedNewCandidate2FromServer,
            ])
        );
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidateErrorsAction({
                candidateId: mockedNewCandidate2.id,
                fieldsErrors: new CreativeCandidateFieldsErrorsState(),
            })
        );
    }));

    it('should correctly map size to backend', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.editCandidate.and
            .returnValue(of(mockedCandidate1, asapScheduler))
            .calls.reset();

        const mockedStoreState: CreativeBatchStoreState = new CreativeBatchStoreState();
        mockedStoreState.entity.id = mockedBatchId;
        mockedStoreState.candidates = [mockedCandidate1];

        effect.effect(
            mockedStoreState,
            new EditCreativeCandidateAction({
                candidate: mockedCandidate1,
                changes: mockedSizeOnFrontend,
                requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.editCandidate).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.editCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCandidate1.id,
            {
                ...mockedSizeOnBackend,
                type: mockedCandidate1.type,
            },
            requestStateUpdater
        );
    }));
});
