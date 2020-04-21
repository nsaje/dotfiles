import {UpdateBlacklistStatusesRequestEntry} from './update-blacklist-statuses-request-entry';
import {PublisherTargetingStatus} from '../../../app.constants';

export interface UpdateBlacklistStatusesRequest {
    entries: UpdateBlacklistStatusesRequestEntry[];
    status: PublisherTargetingStatus;
    adGroup?: number;
    campaign?: number;
    account?: number;
}
