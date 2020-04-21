import {PublisherTargetingStatus} from '../../../app.constants';

export interface PublisherBlacklistAction {
    name: string;
    status: PublisherTargetingStatus;
    permissions?: string[];
}
