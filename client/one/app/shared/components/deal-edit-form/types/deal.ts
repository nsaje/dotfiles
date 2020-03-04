export interface Deal {
    id: string;
    agencyId: string | null;
    accountId: string | null;
    dealId: string;
    description: string;
    name: string;
    source: string;
    floorPrice: string;
    validFromDate?: Date;
    validToDate?: Date;
    createdDt: Date;
    modifiedDt: Date;
    createdBy: string;
    numOfAccounts: number;
    numOfCampaigns: number;
    numOfAdgroups: number;
}
