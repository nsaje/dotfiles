import {ColDef, ValueFormatterParams, CellClassParams} from 'ag-grid-community';
import {NoteCellComponent} from '../../../../shared/components/smart-grid/components/cell/note-cell/note-cell.component';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/item-scope-cell.component';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {NoteRendererParams} from '../../../../shared/components/smart-grid/components/cell/note-cell/types/note.renderer-params';
import {Credit} from '../../../../core/credits/types/credit';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/types/item-scope.renderer-params';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RefundActionsCellComponent} from './components/refund-actions-cell/refund-actions-cell.component';
import {CreditActionsCellComponent} from './components/credit-actions-cell/credit-actions-cell.component';
import {CreditGridType} from '../../credits.constants';
import {CreditStatus} from '../../../../app.constants';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {LinkCellComponent} from '../../../../shared/components/smart-grid/components/cell/link-cell/link-cell.component';
import {LinkRendererParams} from '../../../../shared/components/smart-grid/components/cell/link-cell/types/link.renderer-params';

const statusCellContent = {
    [CreditStatus.PENDING]: {
        text: 'No',
        class: 'zem-credits-grid__status-cell--pending',
    },
    [CreditStatus.SIGNED]: {
        text: 'Yes',
        class: 'zem-credits-grid__status-cell--signed',
    },
    [CreditStatus.CANCELED]: {
        text: 'Canceled',
        class: 'zem-credits-grid__status-cell--canceled',
    },
};

export const COLUMN_ID: ColDef = {
    headerName: 'ID',
    field: 'id',
    width: 80,
    minWidth: 80,
    resizable: false,
    cellRendererFramework: LinkCellComponent,
    cellRendererParams: {
        getText: item => item.id,
        getLink: item => item.salesforceUrl,
    } as LinkRendererParams<Credit>,
};

export const COLUMN_CREATED_BY: ColDef = {
    headerName: 'Created By',
    width: 150,
    minWidth: 150,
    cellRendererFramework: NoteCellComponent,
    cellRendererParams: {
        getMainContent: item => item.createdBy,
        getNote: item =>
            dateTimeFormatter('MM/DD/YYYY')({value: item.createdOn}),
    } as NoteRendererParams<Credit>,
};

export const COLUMN_VALID_FROM: ColDef = {
    headerName: 'Valid from',
    field: 'startDate',
    width: 100,
    minWidth: 100,
    resizable: false,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};
export const COLUMN_VALID_TO: ColDef = {
    headerName: 'Valid to',
    field: 'endDate',
    width: 100,
    minWidth: 100,
    resizable: false,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};

export const COLUMN_SIGNED: ColDef = {
    headerName: 'Signed',
    field: 'status',
    width: 80,
    minWidth: 80,
    resizable: false,
    cellClass: (params: CellClassParams) => {
        if (!isDefined(statusCellContent[params.value])) {
            return '';
        }
        return statusCellContent[params.value].class;
    },
    valueFormatter: (params: ValueFormatterParams) => {
        if (!isDefined(statusCellContent[params.value])) {
            return params.value;
        }
        return statusCellContent[params.value].text;
    },
};

export const COLUMN_CURRENCY: ColDef = {
    headerName: 'Currency',
    field: 'currency',
    width: 80,
    minWidth: 80,
    resizable: false,
};

export const COLUMN_LICENSE_FEE: ColDef = {
    headerName: 'License fee',
    field: 'licenseFee',
    width: 80,
    minWidth: 80,
    resizable: false,
    valueFormatter: params => {
        return `${params.value}%`;
    },
};

export const COLUMN_SERVICE_FEE: ColDef = {
    headerName: 'Service fee',
    field: 'serviceFee',
    width: 80,
    minWidth: 80,
    resizable: false,
    valueFormatter: params => {
        return `${params.value}%`;
    },
};

export const COLUMN_AMOUNT: ColDef = {
    headerName: 'Credit Amount',
    field: 'total',
    width: 120,
    minWidth: 120,
    resizable: false,
    valueFormatter: params => {
        return getValueInCurrency(params.value, params.data.currency);
    },
};

export const COLUMN_AMOUNT_PAST: ColDef = {
    ...COLUMN_AMOUNT,
    headerName: 'Total Credit Amount',
};

export const COLUMN_ALLOCATED: ColDef = {
    headerName: 'Allocated budgets',
    width: 120,
    minWidth: 120,
    resizable: false,
    cellRendererFramework: NoteCellComponent,
    cellRendererParams: {
        getMainContent: item =>
            getValueInCurrency(item.allocated, item.currency),
        getNote: item => `(${item.numOfBudgets} budget items)`,
    } as NoteRendererParams<Credit>,
};

export const COLUMN_AVAILABLE: ColDef = {
    headerName: 'Available Credit',
    field: 'available',
    width: 120,
    minWidth: 120,
    resizable: false,
    valueFormatter: params => {
        return getValueInCurrency(params.value, params.data.currency);
    },
};

export const COLUMN_SCOPE: ColDef = {
    headerName: 'Scope',
    minWidth: 200,
    cellRendererFramework: ItemScopeCellComponent,
    cellRendererParams: {
        getAgencyLink: item => {
            return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
        },
        getAccountLink: item => {
            return `/v2/analytics/account/${item.accountId}`;
        },
    } as ItemScopeRendererParams<Credit>,
};

export const COLUMN_NOTES: ColDef = {
    headerName: 'Notes',
    field: 'comment',
    width: 80,
    minWidth: 80,
    resizable: false,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Comment,
        },
    } as IconTooltipRendererParams<string, Credit, any>,
};

export const COLUMN_ACTION_CREDIT: ColDef = {
    headerName: 'Credit Actions',
    cellRendererFramework: CreditActionsCellComponent,
    pinned: 'right',
    maxWidth: 100,
    minWidth: 100,
    resizable: false,
};

export const COLUMN_ACTION_REFUND: ColDef = {
    headerName: 'Refund Actions',
    cellRendererFramework: RefundActionsCellComponent,
    cellRendererParams: {
        creditGridType: CreditGridType.ACTIVE,
    },
    pinned: 'right',
    maxWidth: 100,
    minWidth: 100,
    resizable: false,
};

export const COLUMN_ACTION_REFUND_PAST: ColDef = {
    ...COLUMN_ACTION_REFUND,
    cellRendererParams: {
        creditGridType: CreditGridType.PAST,
    },
};
