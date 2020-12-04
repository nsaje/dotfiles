import {TrackerEventType, TrackerMethod} from './content-ad.constants';

export const TRACKER_EVENT_TYPE_NAMES: {
    [key in TrackerEventType]: string;
} = {
    [TrackerEventType.IMPRESSION]: 'Impression',
    [TrackerEventType.VIEWABILITY]: 'Viewability',
};

export const TRACKER_METHOD_NAMES: {
    [key in TrackerMethod]: string;
} = {
    [TrackerMethod.IMG]: 'Image Pixel',
    [TrackerMethod.JS]: 'Javascript Tag',
};

export const TRACKER_EVENT_TYPE_METHODS: {
    [key in TrackerEventType]: TrackerMethod[];
} = {
    [TrackerEventType.IMPRESSION]: [TrackerMethod.IMG, TrackerMethod.JS],
    [TrackerEventType.VIEWABILITY]: [TrackerMethod.IMG],
};

export const TRACKER_EVENT_TYPE_OPTIONS: {
    value: TrackerEventType;
    name: string;
}[] = [
    {
        value: TrackerEventType.IMPRESSION,
        name: TRACKER_EVENT_TYPE_NAMES[TrackerEventType.IMPRESSION],
    },
    {
        value: TrackerEventType.VIEWABILITY,
        name: TRACKER_EVENT_TYPE_NAMES[TrackerEventType.VIEWABILITY],
    },
];

export const TRACKER_METHOD_OPTIONS: {
    value: TrackerMethod;
    name: string;
}[] = [
    {value: TrackerMethod.IMG, name: TRACKER_METHOD_NAMES[TrackerMethod.IMG]},
    {value: TrackerMethod.JS, name: TRACKER_METHOD_NAMES[TrackerMethod.JS]},
];

export const MAX_TRACKERS_LIMIT = 3;
