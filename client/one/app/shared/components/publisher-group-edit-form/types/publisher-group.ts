export interface PublisherGroup {
    id: string;
    name: string;
    accountId: string;
    agencyId: string;
    includeSubdomains: boolean;
    implicit: boolean;
    size: number;
    modified: Date;
    created: Date;
    type: string;
    level: string;
    levelName: string;
    levelId: number;
    entries: File;
}
