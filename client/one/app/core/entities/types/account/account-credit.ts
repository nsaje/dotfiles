import {Currency, AccountCreditStatus} from '../../../../app.constants';

export interface AccountCredit {
    id: string;
    createdOn: Date;
    startDate: Date;
    endDate: Date;
    total: string;
    allocated: string;
    available: string;
    licenseFee: string;
    status: AccountCreditStatus;
    currency: Currency;
    comment: string;
    isAvailable: boolean;
    isAgency: boolean;
}
