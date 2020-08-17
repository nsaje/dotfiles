import {User} from '../../users/types/user';

export class AuthStoreState {
    user: User = {
        id: null,
        email: null,
        firstName: null,
        lastName: null,
        name: null,
        status: null,
        agencies: [],
        timezoneOffset: null,
        intercomUserHash: null,
        defaultCsvSeparator: null,
        defaultCsvDecimalSeparator: null,
        permissions: [],
        entityPermissions: [],
    };
    permissions: string[] = null;
    internalPermissions: string[] = null;
}
