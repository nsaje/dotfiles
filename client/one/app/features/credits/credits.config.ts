import {PaginationState} from '../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../shared/components/smart-grid/types/pagination-options';

export const ACTIVE_PAGINATION_URL_PARAMS: {
    [key: string]: keyof PaginationState;
} = {activePage: 'page', activePageSize: 'pageSize'};

export const PAST_PAGINATION_URL_PARAMS: {
    [key: string]: keyof PaginationState;
} = {pastPage: 'page', pastPageSize: 'pageSize'};

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
