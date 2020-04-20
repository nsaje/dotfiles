export interface Deal {
    id: string;
    dealId: string;
    agencyId: string | null;
    agencyName: string | null;
    accountId: string | null;
    accountName: string | null;
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
