import {TrackerEventType, TrackerMethod} from '../content-ad.constants';

export interface ContentAdTracker {
    eventType: TrackerEventType;
    method: TrackerMethod;
    url: string;
    fallbackUrl?: string;
    trackerOptional: boolean;
}
