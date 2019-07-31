import {AccountCredit} from '../../../core/entities/types/account/account-credit';
import {Omit} from '../../../shared/types/omit';

export interface FormattedAccountCredit
    extends Omit<AccountCredit, 'createdOn' | 'startDate' | 'endDate'> {
    createdOn: string;
    startDate: string;
    endDate: string;
}
