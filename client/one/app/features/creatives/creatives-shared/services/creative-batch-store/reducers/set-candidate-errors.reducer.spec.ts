import {
    SetCandidateErrorsAction,
    SetCandidateErrorsActionReducer,
} from './set-candidate-errors.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidateFieldsErrorsState} from '../../../types/creative-candidate-fields-errors-state';

describe('SetCandidateErrorsAction', () => {
    let reducer: SetCandidateErrorsActionReducer;
    const mockedCandidateId = '1';
    const mockedErrors: CreativeCandidateFieldsErrorsState = {
        ...new CreativeCandidateFieldsErrorsState(),
        url: ['This URL is not correct'],
    };

    beforeEach(() => {
        reducer = new SetCandidateErrorsActionReducer();
    });

    it('should correctly set errors', () => {
        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetCandidateErrorsAction({
                candidateId: mockedCandidateId,
                fieldsErrors: mockedErrors,
            })
        );

        expect(state.candidateErrors[mockedCandidateId]).toEqual(mockedErrors);
    });
});
