import {RequestState} from '../../../../shared/types/request-state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {UsersStoreFieldsErrorsState} from './users.store.fields-errors-state';
import {User} from '../../../../core/users/types/user';
import {Account} from '../../../../core/entities/types/account/account';
import {EntityPermissionSelection} from '../../components/entity-permission-selector/types/entity-permission-selection';

export class UsersStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    hasAllAccountsScope: boolean = null;
    entities: User[] = [];
    activeEntity = {
        entity: {
            id: null,
            email: null,
            firstName: '',
            lastName: '',
            entityPermissions: [],
        } as User,
        scopeState: null as ScopeSelectorState,
        entityAccounts: [] as Account[],
        selectedAccounts: [] as Account[],
        selectedEntityPermissions: {} as EntityPermissionSelection,
        isReadOnly: null as boolean,
        fieldsErrors: new UsersStoreFieldsErrorsState(),
    };
    accounts: Account[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    requests = {
        list: {} as RequestState,
        create: {} as RequestState,
        get: {} as RequestState,
        edit: {} as RequestState,
        remove: {} as RequestState,
        validate: {} as RequestState,
    };
}
