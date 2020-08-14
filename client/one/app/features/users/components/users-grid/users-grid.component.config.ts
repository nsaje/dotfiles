import {ColDef} from 'ag-grid-community';
import {EntityPermission} from '../../../../core/users/types/entity-permission';
import {isDefined, isNotEmpty} from '../../../../shared/helpers/common.helpers';
import {User} from '../../../../core/users/types/user';
import {InfoCellComponent} from '../../../../shared/components/smart-grid/components/cell/info-cell/info-cell.component';
import {InfoCellRendererParams} from '../../../../shared/components/smart-grid/components/cell/info-cell/types/info-cell.renderer-params';
import {UsersView} from '../../views/users.view';
import {
    GENERAL_PERMISSIONS,
    REPORTING_PERMISSIONS,
    STATUS_VALUE_TO_NAME,
} from '../../users.config';
import {UserActionsCellComponent} from '../user-actions-cell/user-actions-cell.component';
import {
    getPermissionsText,
    isAccountManager,
} from './helpers/users-grid.helpers';
import {UserStatus} from '../../../../app.constants';

export const COLUMN_NAME: ColDef = {
    headerName: 'Name',
    valueGetter: nameGetter,
    width: 100,
    minWidth: 100,
};

export const COLUMN_EMAIL: ColDef = {
    headerName: 'Email',
    field: 'email',
    width: 180,
    minWidth: 180,
};

export const COLUMN_STATUS: ColDef = {
    headerName: 'Status',
    field: 'status',
    valueFormatter: statusFormatter,
    width: 120,
    minWidth: 120,
};

export const COLUMN_ACCESS: ColDef = {
    headerName: 'Access',
    field: 'entityPermissions',
    valueFormatter: accessFormatter,
    width: 70,
    minWidth: 70,
};

export const COLUMN_PERMISSIONS: ColDef = {
    headerName: 'Permissions',
    field: 'entityPermissions',
    cellRendererFramework: InfoCellComponent,
    cellRendererParams: {
        getMainContent: getGeneralPermissionsText,
        getInfoText: getPermissionTooltip,
    } as InfoCellRendererParams<User, UsersView>,
    width: 200,
    minWidth: 200,
    resizable: true,
};

export const COLUMN_REPORTS: ColDef = {
    headerName: 'Reports',
    field: 'entityPermissions',
    cellRendererFramework: InfoCellComponent,
    cellRendererParams: {
        getMainContent: getReportingPermissionsText,
        getInfoText: getPermissionTooltip,
    } as InfoCellRendererParams<User, UsersView>,
    width: 200,
    minWidth: 200,
    resizable: true,
};

export const COLUMN_ACTIONS: ColDef = {
    headerName: '',
    cellRendererFramework: UserActionsCellComponent,
    pinned: 'right',
    maxWidth: 105,
    minWidth: 105,
    resizable: false,
};

function statusFormatter(params: {value: UserStatus}): string {
    return STATUS_VALUE_TO_NAME[params.value] || 'N/A';
}

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

function getGeneralPermissionsText(
    user: User,
    componentParent: UsersView
): string {
    return getPermissionsText(
        user,
        componentParent.store.state.accountId,
        GENERAL_PERMISSIONS
    );
}

function getReportingPermissionsText(
    user: User,
    componentParent: UsersView
): string {
    return getPermissionsText(
        user,
        componentParent.store.state.accountId,
        REPORTING_PERMISSIONS
    );
}

function getPermissionTooltip(user: User, componentParent: UsersView): string {
    const accountId: string = componentParent.store.state.accountId;
    if (isAccountManager(user) && !isDefined(accountId)) {
        return 'This user has access to one or more agency\'s accounts. To review user\'s permissions, select one of the user\'s accounts in the account selector on the left side of the screen.';
    } else {
        return undefined;
    }
}
