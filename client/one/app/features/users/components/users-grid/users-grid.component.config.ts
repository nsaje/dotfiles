import {ColDef} from 'ag-grid-community';
import {EntityPermission} from '../../../../core/users/types/entity-permission';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {Account} from '../../../../core/entities/types/account/account';
import {User} from '../../../../core/users/types/user';
import {UsersView} from '../../views/users.view';
import {
    GENERAL_PERMISSIONS,
    REPORTING_PERMISSIONS,
    STATUS_VALUE_TO_NAME,
} from '../../users.config';
import {UserActionsCellComponent} from '../user-actions-cell/user-actions-cell.component';
import {
    getPermissionsLevel,
    getPermissionsText,
} from './helpers/users-grid.helpers';
import {UserStatus} from '../../../../app.constants';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {
    IconTooltipCellIcon,
    IconTooltipCellTextStyleClass,
} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {IconTooltipDisplayOptions} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip-display-options';
import {DisplayedEntityPermissionValue} from '../../types/displayed-entity-permission-value';
import {
    isAccountManager,
    isAgencyManager,
    isInternalUser,
} from '../../helpers/users.helpers';
import {distinct} from '../../../../shared/helpers/array.helpers';

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
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Comment,
            placement: 'bottom',
        },
        getCellDisplayOptions: getAccessCellDisplayOptions,
    } as IconTooltipRendererParams<Account[], User, UsersView>,
    width: 100,
    minWidth: 100,
};

export const COLUMN_PERMISSIONS: ColDef = {
    headerName: 'Permissions',
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Info,
            placement: 'bottom',
        },
        getCellDisplayOptions: getGeneralPermissionsCellDisplayOptions,
    } as IconTooltipRendererParams<string, User, UsersView>,
    width: 200,
    minWidth: 200,
    resizable: true,
};

export const COLUMN_REPORTS: ColDef = {
    headerName: 'Reports',
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Info,
            placement: 'bottom',
        },
        getCellDisplayOptions: getReportingPermissionsCellDisplayOptions,
    } as IconTooltipRendererParams<string, User, UsersView>,
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

function nameGetter(params: {data: User}): string {
    return `${params?.data?.firstName || ''} ${params?.data?.lastName || ''}`;
}

function getAccessCellDisplayOptions(
    user: User,
    componentParent: UsersView
): Partial<IconTooltipDisplayOptions<Account[]>> {
    return {
        text: getPermissionsLevel(user),
        iconTooltip: getAccounts(user, componentParent),
    };
}

function getAccounts(user: User, componentParent: UsersView): Account[] {
    const entityPermissions: EntityPermission[] = user.entityPermissions || [];

    // These 3 possibilities should be mutually exclusive, but we still need to check because there could be inconsistent data in the DB
    if (
        !isInternalUser(user) &&
        !isAgencyManager(user) &&
        isAccountManager(user)
    ) {
        return distinct(
            entityPermissions
                .filter(ep => ep.accountId)
                .map(ep => getAccountById(componentParent, ep.accountId))
                .filter(accountName => isDefined(accountName))
        );
    } else {
        return undefined;
    }
}

function getAccountById(
    componentParent: UsersView,
    accountId: string
): Account | undefined {
    return componentParent.store.state.accounts?.find(
        account => account.id === accountId
    );
}

function getGeneralPermissionsCellDisplayOptions(
    user: User,
    componentParent: UsersView
): Partial<IconTooltipDisplayOptions<string>> {
    return getPermissionsCellDisplayOptions(
        user,
        componentParent,
        GENERAL_PERMISSIONS
    );
}

function getReportingPermissionsCellDisplayOptions(
    user: User,
    componentParent: UsersView
): Partial<IconTooltipDisplayOptions<string>> {
    return getPermissionsCellDisplayOptions(
        user,
        componentParent,
        REPORTING_PERMISSIONS
    );
}

function getPermissionsCellDisplayOptions(
    user: User,
    componentParent: UsersView,
    permissionsInColumn: DisplayedEntityPermissionValue[]
): Partial<IconTooltipDisplayOptions<string>> {
    const accountId: string = componentParent.store.state.accountId;
    if (isAccountManager(user) && !isDefined(accountId)) {
        return {
            textStyleClass: IconTooltipCellTextStyleClass.Lighter,
            iconTooltip:
                "This user has access to one or more agency's accounts. To review user's permissions, select one of the user's accounts in the account selector on the left side of the screen.",
            text: 'N/A',
        };
    } else {
        const text = getPermissionsText(
            user,
            componentParent.store.state.accountId,
            permissionsInColumn
        );
        return {
            text,
            textTooltip: text,
        };
    }
}
