import {ColDef} from 'ag-grid-community';
import {EntityPermission} from '../../../../core/users/types/entity-permission';
import {isNotEmpty} from '../../../../shared/helpers/common.helpers';
import {User} from '../../../../core/users/types/user';
import {CreditActionsCellComponent} from '../../../credits/components/credits-grid/components/credit-actions-cell/credit-actions-cell.component';
import {UserActionsCellComponent} from '../user-actions-cell/user-actions-cell.component';

export const COLUMN_NAME: ColDef = {
    headerName: 'Name',
    valueGetter: nameGetter,
};

export const COLUMN_EMAIL: ColDef = {
    headerName: 'Email',
    field: 'email',
};

export const COLUMN_ACCESS: ColDef = {
    headerName: 'Access',
    field: 'entityPermissions',
    valueFormatter: accessFormatter,
};

export const COLUMN_ACTIONS: ColDef = {
    headerName: '',
    cellRendererFramework: UserActionsCellComponent,
    pinned: 'right',
    maxWidth: 75,
    minWidth: 75,
    resizable: false,
};

function accessFormatter(params: {value: EntityPermission[]}): string {
    const value: EntityPermission[] = params.value;

    if (isNotEmpty(value.filter(ep => ep.accountId))) {
        return 'Account';
    } else if (isNotEmpty(value.filter(ep => ep.agencyId))) {
        return 'Agency';
    } else if (isNotEmpty(value)) {
        return 'All accounts';
    } else {
        return 'None'; // This should never happen, but we can handle it just in case
    }
}

function nameGetter(params: {data: User}): string {
    return `${params?.data?.firstName || ''} ${params?.data?.lastName || ''}`;
}
