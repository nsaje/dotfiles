import {TrackerEventType, TrackerMethod} from '../creatives.constants';

export interface Tracker {
    eventType: TrackerEventType;
    method: TrackerMethod;
    url: string;
    fallbackUrl?: string;
    trackerOptional: boolean;
}
