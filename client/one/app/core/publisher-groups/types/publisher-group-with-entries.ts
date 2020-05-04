import {Publisher} from '../../publishers/types/publisher';

export interface PublisherGroupWithEntries {
    id?: string;
    name: string;
    accountId?: string;
    agencyId?: string;
    defaultIncludeSubdomains: boolean;
    entries: Publisher[];
}
