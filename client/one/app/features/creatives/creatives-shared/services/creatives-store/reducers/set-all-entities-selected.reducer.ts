import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';

export class SetAllEntitiesSelectedAction extends StoreAction<boolean> {}

// tslint:disable-next-line: max-classes-per-file
export class SetAllEntitiesSelectedActionReducer extends StoreReducer<
    CreativesStoreState,
    SetAllEntitiesSelectedAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetAllEntitiesSelectedAction
    ): CreativesStoreState {
        return {
            ...state,
            selectedEntityIds: action.payload
                ? state.entities.map(entity => entity.id)
                : [],
        };
    }
}
