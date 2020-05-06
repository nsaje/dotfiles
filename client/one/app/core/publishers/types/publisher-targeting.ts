import {Publisher} from './publisher';
import {PublisherTargetingStatus} from '../../../app.constants';

export interface PublisherTargeting {
    entries: Publisher[];
    status: PublisherTargetingStatus;
    adGroup?: number;
    campaign?: number;
    account?: number;
}
