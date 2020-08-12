import {PaginationState} from '../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../shared/components/smart-grid/types/pagination-options';
import {EntityPermissionValue} from '../../core/users/types/entity-permission-value';
import {DisplayedEntityPermissionValue} from './types/displayed-entity-permission-value';
import {UserStatus} from '../../app.constants';

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

export const GENERAL_PERMISSIONS: EntityPermissionValue[] = [
    'write',
    'budget',
    'user',
];
export const REPORTING_PERMISSIONS: DisplayedEntityPermissionValue[] = [
    'total_spend',
    'agency_spend_margin',
    'media_cost_data_cost_licence_fee',
    'base_costs_service_fee',
];

export const CONFIGURABLE_PERMISSIONS: EntityPermissionValue[] = [
    ...GENERAL_PERMISSIONS,
    ...(<EntityPermissionValue[]>(
        REPORTING_PERMISSIONS.filter(p => p !== 'total_spend')
    )),
];

export const ENTITY_PERMISSION_VALUE_TO_NAME: {
    [key in DisplayedEntityPermissionValue]: string;
} = {
    total_spend: 'Total spend',
    read: 'Read',
    write: 'Edit',
    user: 'Manage users',
    budget: 'Manage budget',
    budget_margin: 'Manage budget margin',
    agency_spend_margin: 'Agency spend and margin',
    media_cost_data_cost_licence_fee: 'Media cost, data cost and license fee',
    base_costs_service_fee: 'Base media and data cost and service fee',
};

export const ENTITY_PERMISSION_VALUE_TO_SHORT_NAME: {
    [key in DisplayedEntityPermissionValue]: string;
} = {
    ...ENTITY_PERMISSION_VALUE_TO_NAME,
    agency_spend_margin: 'Campaign margin',
    media_cost_data_cost_licence_fee: 'License fee',
    base_costs_service_fee: 'Service fee',
};

export const ENTITY_PERMISSION_VALUE_TO_DESCRIPTION: {
    [key in EntityPermissionValue]: string;
} = {
    read: '',
    write: 'Can edit accounts, campaigns, ad groups or ads.',
    user: 'Can add, delete users and change users permissions.',
    budget: 'Can allocate budget to campaign',
    budget_margin: '',
    agency_spend_margin: '',
    media_cost_data_cost_licence_fee: '',
    base_costs_service_fee: '',
};

export const STATUS_VALUE_TO_NAME: {
    [key in UserStatus]: string;
} = {
    [UserStatus.INVITATION_PENDING]: 'Invitation Pending',
    [UserStatus.ACTIVE]: 'Active',
};
