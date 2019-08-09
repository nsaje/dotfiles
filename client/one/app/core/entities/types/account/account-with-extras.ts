import {Account} from './account';
import {AccountExtras} from './account-extras';

export interface AccountWithExtras {
    account: Account;
    extras: AccountExtras;
}
