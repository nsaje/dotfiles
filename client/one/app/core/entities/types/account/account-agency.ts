import {AccountType} from '../../../../app.constants';

export interface AccountAgency {
    id: string;
    name: string;
    salesRepresentative: string;
    csRepresentative: string;
    obRepresentative: string;
    defaultAccountType: AccountType;
}
