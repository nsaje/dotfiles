import {StoreAction} from '../../../../shared/services/store/store.action';

import {StoreReducer} from '../../../../shared/services/store/store.reducer';
import {User} from '../../../users/types/user';
import {AuthStoreState} from '../auth.store.state';
import {Permission} from '../../../users/types/permission';

export class SetCurrentUserAction extends StoreAction<User> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCurrentUserActionReducer extends StoreReducer<
    AuthStoreState,
    SetCurrentUserAction
> {
    reduce(
        state: AuthStoreState,
        action: SetCurrentUserAction
    ): AuthStoreState {
        return {
            ...state,
            user: action.payload,
            permissions: action.payload.permissions.map(x => x.permission),
            internalPermissions: action.payload.permissions
                .filter(x => !x.isPublic)
                .map(x => x.permission),
        };
    }
}
