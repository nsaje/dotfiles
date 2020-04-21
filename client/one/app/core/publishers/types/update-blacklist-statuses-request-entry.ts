import {PublisherInfo} from './publisher-info';

export interface UpdateBlacklistStatusesRequestEntry extends PublisherInfo {
    includeSubdomains?: boolean;
}
