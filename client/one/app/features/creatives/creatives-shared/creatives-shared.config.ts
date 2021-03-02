import {PaginationOptions} from '../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../shared/components/smart-grid/types/pagination-state';
import {
    AdSize,
    AdType,
    CreativeBatchType,
    ImageCrop,
} from '../../../app.constants';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../core/creatives/creatives.constants';
import {AdSizeConfig} from './types/ad-size-config';

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

export const CREATIVE_TYPES: {
    id: AdType;
    name: string;
    batchType: CreativeBatchType;
}[] = [
    {id: AdType.CONTENT, name: 'Content', batchType: CreativeBatchType.NATIVE},
    {id: AdType.VIDEO, name: 'Video', batchType: CreativeBatchType.VIDEO},
    {id: AdType.IMAGE, name: 'Image', batchType: CreativeBatchType.DISPLAY},
    {id: AdType.AD_TAG, name: 'Ad tag', batchType: CreativeBatchType.DISPLAY},
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

export const IMAGE_CROPS: {name: string; value: ImageCrop}[] = [
    {name: 'Center', value: ImageCrop.CENTER},
    {name: 'Faces', value: ImageCrop.FACES},
    {name: 'Entropy', value: ImageCrop.ENTROPY},
    {name: 'Left', value: ImageCrop.LEFT},
    {name: 'Right', value: ImageCrop.RIGHT},
    {name: 'Top', value: ImageCrop.TOP},
    {name: 'Bottom', value: ImageCrop.BOTTOM},
];

export const CALLS_TO_ACTION: {name: string; value: string}[] = [
    'Read More',
    'Book Now',
    'Contact Us',
    'Learn More',
    'Shop Now',
    'Sign Up',
    'Watch More',
    'Download',
    'Apply Now',
    'Bet Now',
    'Buy Now',
    'Compare',
    'Directions',
    'Donate Now',
    'Enroll Now',
    'Follow Now',
    'Get App',
    'Get Coupon',
    'Get Now',
    'Get Offer',
    'Get Quote',
    'Get Rates',
    'Get Sample',
    'Install',
    'Join Now',
    'Launch',
    'Listen Now',
    'Play Now',
    'Play Game',
    'Record Now',
    'Register',
    'Remind Me',
    'Save Now',
    'Sell Now',
    'Subscribe',
    'Try Now',
    'Use App',
    'Vote Now',
    'Watch Now',
].map(x => ({name: x, value: x}));

export const AD_SIZES: AdSizeConfig[] = [
    {size: AdSize.MOBILE_LEADERBOARD, width: 320, height: 50},
    {size: AdSize.INLINE_RECTANGLE, width: 300, height: 250},
    {size: AdSize.LEADERBOARD, width: 728, height: 90},
    {size: AdSize.LARGE_RECTANGLE, width: 336, height: 280},
    {size: AdSize.HALF_PAGE, width: 300, height: 600},
    {size: AdSize.WIDESKYSCRAPER, width: 120, height: 600},
    {size: AdSize.LARGE_MOBILE_BANNER, width: 320, height: 100},
    {size: AdSize.BANNER, width: 468, height: 60},
    {size: AdSize.PORTRAIT, width: 300, height: 1050},
    {size: AdSize.LARGE_LEADERBOARD, width: 970, height: 90},
    {size: AdSize.BILLBOARD, width: 970, height: 250},
    {size: AdSize.SQUARE, width: 250, height: 250},
    {size: AdSize.SMALL_SQUARE, width: 200, height: 200},
    {size: AdSize.SMALL_RECTANGLE, width: 180, height: 150},
    {size: AdSize.BUTTON, width: 125, height: 125},
].map(x => ({...x, name: `${x.width}x${x.height}`}));
