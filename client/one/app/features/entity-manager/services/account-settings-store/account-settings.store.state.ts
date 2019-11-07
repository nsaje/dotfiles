import {Account} from '../../../../core/entities/types/account/account';
import {AccountExtras} from '../../../../core/entities/types/account/account-extras';
import {RequestState} from '../../../../shared/types/request-state';
import {AccountSettingsStoreFieldsErrorsState} from './account-settings.store.fields-errors-state';
import {Deal} from '../../../../core/deals/types/deal';

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
        deals: [],
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
    availableDeals: Deal[] = [];
    fieldsErrors = new AccountSettingsStoreFieldsErrorsState();
    dealsRequests = {
        list: {} as RequestState,
    };
    requests = {
        defaults: {} as RequestState,
        get: {} as RequestState,
        validate: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
    };
}
