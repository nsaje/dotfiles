import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';

export class SetScopeAction extends StoreAction<ScopeParams> {}

// tslint:disable-next-line: max-classes-per-file
export class SetScopeActionReducer extends StoreReducer<
    CreativesStoreState,
    SetScopeAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetScopeAction
    ): CreativesStoreState {
        return {
            ...state,
            scope: action.payload,
        };
    }
}
