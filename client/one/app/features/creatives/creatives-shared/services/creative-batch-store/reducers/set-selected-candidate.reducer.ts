import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';

export class SetSelectedCandidateAction extends StoreAction<
    CreativeCandidate
> {}

// tslint:disable-next-line: max-classes-per-file
export class SetSelectedCandidateActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetSelectedCandidateAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetSelectedCandidateAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            selectedCandidateId: action.payload?.id,
        };
    }
}
