import {PaginationState} from '../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../shared/components/smart-grid/types/pagination-options';
import {EntityPermissionValue} from '../../core/users/types/entity-permission-value';

export const PAGINATION_URL_PARAMS = ['page', 'pageSize'];

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

export const ENTITY_PERMISSION_VALUE_TO_NAME: {
    [key in EntityPermissionValue]: string;
} = {
    read: 'Read',
    write: 'Edit',
    user: 'Manage users',
    budget: 'Manage budget',
    budget_margin: 'Manage budget margin',
    agency_spend_margin: 'Agency spend and margin',
    media_cost_data_cost_licence_fee: 'Media cost, data cost and licence fee',
};
