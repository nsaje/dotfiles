import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidateFieldsErrorsState} from '../../../types/creative-candidate-fields-errors-state';

export interface SetCandidateErrorsParams {
    candidateId: string;
    fieldsErrors: CreativeCandidateFieldsErrorsState;
}

export class SetCandidateErrorsAction extends StoreAction<
    SetCandidateErrorsParams
> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCandidateErrorsActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetCandidateErrorsAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetCandidateErrorsAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            candidateErrors: {
                ...state.candidateErrors,
                [action.payload.candidateId]: action.payload.fieldsErrors,
            },
        };
    }
}
