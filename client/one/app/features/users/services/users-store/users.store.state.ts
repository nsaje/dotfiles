import {RequestState} from '../../../../shared/types/request-state';
import {User} from '../../../../core/users/types/user';

export class UsersStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    entities: User[] = [];
    requests = {
        list: {} as RequestState,
    };
}
