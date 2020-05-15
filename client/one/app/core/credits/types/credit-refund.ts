export interface CreditRefund {
    id?: string;
    createdBy?: string;
    createdDt?: Date;
    accountId: string;
    creditId?: string;
    startDate: Date;
    endDate?: Date;
    amount: number;
    effectiveMargin: string;
    comment: string;
}
