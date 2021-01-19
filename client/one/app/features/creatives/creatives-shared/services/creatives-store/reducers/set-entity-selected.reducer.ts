import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {SetEntitySelectedParams} from '../../../types/set-entity-selected-params';

export class SetEntitySelectedAction extends StoreAction<
    SetEntitySelectedParams
> {}

// tslint:disable-next-line: max-classes-per-file
export class SetEntitySelectedActionReducer extends StoreReducer<
    CreativesStoreState,
    SetEntitySelectedAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetEntitySelectedAction
    ): CreativesStoreState {
        return {
            ...state,
            selectedEntityIds: this.getNewSelectedEntityIds(
                state,
                action.payload
            ),
        };
    }

    private getNewSelectedEntityIds(
        state: CreativesStoreState,
        change: SetEntitySelectedParams
    ): string[] {
        if (
            change.setSelected &&
            !state.selectedEntityIds.includes(change.entityId) &&
            state.entities.map(entity => entity.id).includes(change.entityId)
        ) {
            return state.selectedEntityIds.concat([change.entityId]);
        } else if (
            !change.setSelected &&
            state.selectedEntityIds.includes(change.entityId)
        ) {
            return state.selectedEntityIds.filter(id => id !== change.entityId);
        } else {
            return state.selectedEntityIds;
        }
    }
}
