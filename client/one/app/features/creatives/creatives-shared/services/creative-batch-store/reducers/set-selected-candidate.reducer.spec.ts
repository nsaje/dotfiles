import {
    SetSelectedCandidateAction,
    SetSelectedCandidateActionReducer,
} from './set-selected-candidate.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';

describe('SetSelectedCandidateActionReducer', () => {
    let reducer: SetSelectedCandidateActionReducer;
    let mockedState: CreativeBatchStoreState;
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
        reducer = new SetSelectedCandidateActionReducer();
        mockedState = new CreativeBatchStoreState();
        mockedState.candidates = mockedCandidates;
    });

    it('should correctly select candidate', () => {
        const candidateToSelect: CreativeCandidate = mockedCandidates[1];
        const state = reducer.reduce(
            mockedState,
            new SetSelectedCandidateAction(candidateToSelect)
        );

        expect(state.selectedCandidateId).toEqual(candidateToSelect.id);
    });

    it('should correctly deselect candidate', () => {
        const mockedState2: CreativeBatchStoreState = {
            ...mockedState,
            selectedCandidateId: mockedCandidates[0].id,
        };

        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetSelectedCandidateAction(undefined)
        );

        expect(state.selectedCandidateId).not.toBeDefined();
    });
});
