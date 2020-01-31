import {Account} from '../../core/entities/types/account/account';

export const accountMock: Account = {
    id: null,
    agencyId: null,
    name: null,
    currency: null,
    frequencyCapping: null,
    accountType: null,
    defaultAccountManager: null,
    defaultSalesRepresentative: null,
    defaultCsRepresentative: null,
    obSalesRepresentative: null,
    obAccountManager: null,
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
    defaultIconUrl: null,
    defaultIconBase64: null,
};
