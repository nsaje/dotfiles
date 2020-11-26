import {ValueFormatterParams, CellClassParams} from 'ag-grid-community';
import {NoteCellComponent} from '../../../../shared/components/smart-grid/components/cells/note-cell/note-cell.component';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {NoteRendererParams} from '../../../../shared/components/smart-grid/components/cells/note-cell/types/note.renderer-params';
import {Credit} from '../../../../core/credits/types/credit';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RefundActionsCellComponent} from './components/refund-actions-cell/refund-actions-cell.component';
import {CreditActionsCellComponent} from './components/credit-actions-cell/credit-actions-cell.component';
import {CreditGridType} from '../../credits.constants';
import {CreditStatus, ViewportBreakpoint} from '../../../../app.constants';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {LinkCellComponent} from '../../../../shared/components/smart-grid/components/cells/link-cell/link-cell.component';
import {LinkRendererParams} from '../../../../shared/components/smart-grid/components/cells/link-cell/types/link.renderer-params';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';

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

export const COLUMN_ID: SmartGridColDef = {
    headerName: 'ID',
    field: 'id',
    width: 80,
    minWidth: 80,
    cellRendererFramework: LinkCellComponent,
    cellRendererParams: {
        getText: params => params.data.id,
        getLink: params => params.data.salesforceUrl,
    } as LinkRendererParams<Credit>,
};

export const COLUMN_CREATED_BY: SmartGridColDef = {
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

export const COLUMN_VALID_FROM: SmartGridColDef = {
    headerName: 'Valid from',
    field: 'startDate',
    width: 100,
    minWidth: 100,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};
export const COLUMN_VALID_TO: SmartGridColDef = {
    headerName: 'Valid to',
    field: 'endDate',
    width: 100,
    minWidth: 100,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};

export const COLUMN_SIGNED: SmartGridColDef = {
    headerName: 'Signed',
    field: 'status',
    width: 80,
    minWidth: 80,
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

export const COLUMN_CURRENCY: SmartGridColDef = {
    headerName: 'Currency',
    field: 'currency',
    width: 80,
    minWidth: 80,
};

export const COLUMN_LICENSE_FEE: SmartGridColDef = {
    headerName: 'License fee',
    field: 'licenseFee',
    width: 85,
    minWidth: 80,
    suppressSizeToFit: true,
    resizable: true,
    valueFormatter: feeFormatter,
};

export const COLUMN_SERVICE_FEE: SmartGridColDef = {
    headerName: 'Service fee',
    field: 'serviceFee',
    width: 85,
    minWidth: 80,
    suppressSizeToFit: true,
    resizable: true,
    valueFormatter: feeFormatter,
};

export const COLUMN_AMOUNT: SmartGridColDef = {
    headerName: 'Credit Amount',
    field: 'total',
    width: 120,
    minWidth: 120,
    valueFormatter: params => {
        return getValueInCurrency(params.value, params.data.currency);
    },
};

export const COLUMN_AMOUNT_PAST: SmartGridColDef = {
    ...COLUMN_AMOUNT,
    width: 135,
    headerName: 'Total Credit Amount',
    suppressSizeToFit: true,
    resizable: true,
};

export const COLUMN_ALLOCATED: SmartGridColDef = {
    headerName: 'Allocated budgets',
    width: 125,
    minWidth: 120,
    suppressSizeToFit: true,
    resizable: true,
    cellRendererFramework: NoteCellComponent,
    cellRendererParams: {
        getMainContent: item =>
            getValueInCurrency(item.allocated, item.currency),
        getNote: item => `(${item.numOfBudgets} budget items)`,
    } as NoteRendererParams<Credit>,
};

export const COLUMN_AVAILABLE: SmartGridColDef = {
    headerName: 'Available Credit',
    field: 'available',
    width: 120,
    minWidth: 120,
    valueFormatter: params => {
        return getValueInCurrency(params.value, params.data.currency);
    },
};

export const COLUMN_SCOPE: SmartGridColDef = {
    headerName: 'Scope',
    minWidth: 180,
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

export const COLUMN_NOTES: SmartGridColDef = {
    headerName: 'Notes',
    field: 'comment',
    width: 80,
    minWidth: 80,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Comment,
        },
    } as IconTooltipRendererParams<string, Credit, any>,
};

export const COLUMN_ACTION_CREDIT: SmartGridColDef = {
    headerName: 'Credit Actions',
    cellRendererFramework: CreditActionsCellComponent,
    pinned: 'right',
    maxWidth: 100,
    minWidth: 100,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};

export const COLUMN_ACTION_REFUND: SmartGridColDef = {
    headerName: 'Refund Actions',
    cellRendererFramework: RefundActionsCellComponent,
    cellRendererParams: {
        creditGridType: CreditGridType.ACTIVE,
    },
    pinned: 'right',
    minWidth: 100,
    width: 110,
    suppressSizeToFit: true,
    resizable: true,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};

export const COLUMN_ACTION_REFUND_PAST: SmartGridColDef = {
    ...COLUMN_ACTION_REFUND,
    cellRendererParams: {
        creditGridType: CreditGridType.PAST,
    },
};

function feeFormatter(params: ValueFormatterParams): string {
    return isDefined(params.value) ? `${params.value}%` : 'N/A';
}
