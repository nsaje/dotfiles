import {
    FetchCreativeCandidatesActionEffect,
    FetchCreativeCandidatesAction,
} from './fetch-creative-candidates.effect';
import {of, asapScheduler} from 'rxjs';
import {fakeAsync, tick} from '@angular/core/testing';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {MAX_LOADED_CANDIDATES} from '../../../creatives-shared.config';

describe('FetchCreativeCandidatesActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let effect: FetchCreativeCandidatesActionEffect;
    let requestStateUpdater: RequestStateUpdater;
    const mockedBatchId = '123';
    const mockedCandidates: CreativeCandidate[] = [
        {
            id: '1',
            title: 'Test candidate 1',
        },
        {
            id: '2',
            title: 'Test candidate 2',
        },
    ];

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'listCandidates',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCreativeCandidatesActionEffect(creativesServiceStub);
    });

    it('should fetch creative candidates via service', fakeAsync(() => {
        const pagination: PaginationState = {
            page: 1,
            pageSize: MAX_LOADED_CANDIDATES,
        };

        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.listCandidates.and
            .returnValue(of(mockedCandidates, asapScheduler))
            .calls.reset();

        effect.effect(
            new CreativeBatchStoreState(),
            new FetchCreativeCandidatesAction({
                batchId: mockedBatchId,
                pagination,
                requestStateUpdater: requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.listCandidates).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.listCandidates).toHaveBeenCalledWith(
            mockedBatchId,
            0,
            pagination.pageSize,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCandidatesAction(mockedCandidates)
        );
    }));
});
