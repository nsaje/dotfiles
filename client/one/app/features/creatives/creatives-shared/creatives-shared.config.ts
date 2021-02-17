import {PaginationOptions} from '../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../shared/components/smart-grid/types/pagination-state';
import {AdType} from '../../../app.constants';

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
