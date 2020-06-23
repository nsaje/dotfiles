import {Currency, CreditStatus} from '../../../app.constants';

export interface Credit {
    id?: string;
    createdBy?: string;
    createdOn?: Date;
    startDate: Date;
    endDate: Date | null;
    total?: string;
    allocated?: string;
    available?: string;
    licenseFee: string;
    serviceFee: string;
    status: CreditStatus;
    currency: Currency;
    accountId?: string | null;
    accountName?: string | null;
    agencyId?: string | null;
    agencyName?: string | null;
    flatFee?: string;
    amount: number;
    contractId: string | null;
    contractNumber: string | null;
    comment: string | null;
    isAvailable?: boolean;
    salesforceUrl?: string;
    numOfBudgets?: number;
}
