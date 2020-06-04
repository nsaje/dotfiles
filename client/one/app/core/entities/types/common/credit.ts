import {Currency, CreditStatus} from '../../../../app.constants';

export interface Credit {
    id: string;
    createdOn: Date;
    status: CreditStatus;
    agencyId: string;
    accountId: string;
    startDate: Date;
    endDate: Date;
    licenseFee: string;
    amount: number;
    total: string;
    allocated: string;
    available: string;
    currency: Currency;
    contractId: string;
    contractNumber: string;
    comment: string;
    salesforceUrl: string;
    isAvailable: boolean;
}
