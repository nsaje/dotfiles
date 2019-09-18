import {Account} from '../../../../core/entities/types/account/account';
import {AccountExtras} from '../../../../core/entities/types/account/account-extras';
import {RequestState} from '../../../../shared/types/request-state';
import {AccountSettingsStoreFieldsErrorsState} from './account-settings.store.fields-errors-state';

export class AccountSettingsStoreState {
    entity: Account = {
        id: null,
        agencyId: null,
        name: null,
        currency: null,
        frequencyCapping: null,
        accountType: null,
        defaultAccountManager: null,
        defaultSalesRepresentative: null,
        defaultCsRepresentative: null,
        obRepresentative: null,
        autoAddNewSources: null,
        salesforceUrl: null,
        archived: null,
        targeting: {
            publisherGroups: {
                included: [],
                excluded: [],
            },
        },
        allowedMediaSources: [],
    };
    extras: AccountExtras = {
        archived: null,
        canArchive: null,
        canRestore: null,
        isExternallyManaged: null,
        agencies: [],
        accountManagers: [],
        salesRepresentatives: [],
        csRepresentatives: [],
        obRepresentatives: [],
        hacks: [],
        deals: [],
        availableMediaSources: [],
    };
    fieldsErrors = new AccountSettingsStoreFieldsErrorsState();
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
    };
}
