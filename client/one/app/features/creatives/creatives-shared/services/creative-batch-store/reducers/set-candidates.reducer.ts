import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';

export class SetCandidatesAction extends StoreAction<CreativeCandidate[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCandidatesActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetCandidatesAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetCandidatesAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            candidates: [...action.payload],
        };
    }
}
