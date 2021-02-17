import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {
    SetCandidatesAction,
    SetCandidatesActionReducer,
} from './set-candidates.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';

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
});
