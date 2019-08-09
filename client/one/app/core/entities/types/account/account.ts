import {Currency, AccountType} from '../../../../app.constants';
import {AccountTargeting} from './account-targeting';
import {AccountMediaSources} from './account-media-sources';

export interface Account {
    id: string;
    agencyId: string;
    name: string;
    currency: Currency;
    frequencyCapping: number;
    accountType: AccountType;
    defaultAccountManager: string;
    defaultSalesRepresentative: string;
    defaultCsRepresentative: string;
    obRepresentative: string;
    autoAddNewSources: boolean;
    salesforceUrl: string;
    archived: boolean;
    targeting: AccountTargeting;
    mediaSources: AccountMediaSources[];
}
