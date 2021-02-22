import {PaginationOptions} from '../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../shared/components/smart-grid/types/pagination-state';
import {AdType} from '../../../app.constants';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../core/creatives/creatives.constants';

export const DEFAULT_PAGINATION: PaginationState = {
    page: 1,
    pageSize: 20,
};

export const DEFAULT_PAGINATION_OPTIONS: PaginationOptions = {
    type: 'server',
    pageSizeOptions: [
        {name: '10', value: 10},
        {name: '20', value: 20},
        {name: '50', value: 50},
    ],
    ...DEFAULT_PAGINATION,
};

export const CREATIVE_TYPES: {id: AdType; name: string}[] = [
    {id: AdType.CONTENT, name: 'Content'},
    {id: AdType.VIDEO, name: 'Video'},
    {id: AdType.IMAGE, name: 'Image'},
    {id: AdType.AD_TAG, name: 'Ad tag'},
];

export const MAX_LOADED_TAGS = 100;
export const MAX_LOADED_CANDIDATES = 100;

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

export const TRACKER_METHOD_EVENT_TYPES: {
    [key in TrackerMethod]: TrackerEventType[];
} = {
    [TrackerMethod.JS]: [TrackerEventType.IMPRESSION],
    [TrackerMethod.IMG]: [
        TrackerEventType.IMPRESSION,
        TrackerEventType.VIEWABILITY,
    ],
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
export const MAX_TRACKERS_EXTRA_LIMIT = 6;
