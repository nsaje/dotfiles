import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {
    SetCandidatesAction,
    SetCandidatesActionReducer,
} from './set-candidates.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {AdSize} from '../../../../../../app.constants';

describe('SetCandidatesActionReducer', () => {
    let reducer: SetCandidatesActionReducer;
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

    const mockedSizeOnBackend: Partial<CreativeCandidate> = {
        imageWidth: 300,
        imageHeight: 600,
    };
    const mockedSizeOnFrontend: Partial<CreativeCandidate> = {
        size: AdSize.HALF_PAGE,
    };
    const mockedCandidateWithSizeOnBackend: CreativeCandidate = {
        ...mockedCandidates[0],
        ...mockedSizeOnBackend,
    };
    const mockedCandidateWithSizeOnFrontend: CreativeCandidate = {
        ...mockedCandidates[0],
        ...mockedSizeOnFrontend,
    };

    beforeEach(() => {
        reducer = new SetCandidatesActionReducer();
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetCandidatesAction(mockedCandidates)
        );

        expect(state.candidates).toEqual(mockedCandidates);
    });

    it('should correctly map size to frontend', () => {
        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetCandidatesAction([mockedCandidateWithSizeOnBackend])
        );

        expect(state.candidates).toEqual([mockedCandidateWithSizeOnFrontend]);
    });
});
