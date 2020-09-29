import {User} from '../../users/types/user';
import {RequestState} from '../../../shared/types/request-state';

export class AuthStoreState {
    user: User = {
        id: null,
        email: null,
        firstName: null,
        lastName: null,
        name: null,
        status: null,
        timezoneOffset: null,
        intercomUserHash: null,
        defaultCsvSeparator: null,
        defaultCsvDecimalSeparator: null,
        permissions: [],
        entityPermissions: [],
    };
    permissions: string[] = null;
    internalPermissions: string[] = null;
    requests = {
        current: {} as RequestState,
    };
}
