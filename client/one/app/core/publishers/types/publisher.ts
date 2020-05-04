export interface Publisher {
    id?: number;
    source: string;
    publisher: string;
    placement?: string;
    publisherGroupId?: string;
    includeSubdomains?: boolean;
}
