import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {CellClassParams, CellClickedEvent} from 'ag-grid-community';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {Deal} from '../../../../core/deals/types/deal';
import {DealActionsCellComponent} from '../deal-actions-cell/deal-actions-cell.component';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {DealConnectionType} from '../../types/deal-connection-type';
import {DealsView} from '../../views/deals/deals.view';
import {ViewportBreakpoint} from '../../../../app.constants';

export const COLUMN_ID: SmartGridColDef = {
    headerName: 'Id',
    field: 'id',
    minWidth: 50,
    width: 80,
    suppressSizeToFit: true,
    resizable: true,
};

export const COLUMN_DEAL_NAME: SmartGridColDef = {
    headerName: 'Deal name',
    field: 'name',
    minWidth: 120,
    width: 200,
    suppressSizeToFit: true,
    resizable: true,
};

export const COLUMN_DEAL_ID: SmartGridColDef = {
    headerName: 'Deal Id',
    field: 'dealId',
    minWidth: 120,
    width: 140,
    suppressSizeToFit: true,
    resizable: true,
};

export const COLUMN_SOURCE: SmartGridColDef = {
    headerName: 'Source',
    field: 'source',
    minWidth: 90,
};

export const COLUMN_FLOOR_PRICE: SmartGridColDef = {
    headerName: 'Floor price',
    field: 'floorPrice',
    width: 90,
    suppressSizeToFit: true,
};

export const COLUMN_VALID_FROM: SmartGridColDef = {
    headerName: 'Valid from',
    field: 'validFromDate',
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
    width: 110,
    suppressSizeToFit: true,
};

export const COLUMN_VALID_TO: SmartGridColDef = {
    headerName: 'Valid to',
    field: 'validToDate',
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
    width: 110,
    suppressSizeToFit: true,
};

export const COLUMN_SCOPE: SmartGridColDef = {
    headerName: 'Scope',
    cellRendererFramework: ItemScopeCellComponent,
    cellRendererParams: {
        getAgencyLink: item => {
            return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
        },
        getAccountLink: item => {
            return `/v2/analytics/account/${item.accountId}`;
        },
    } as ItemScopeRendererParams<Deal>,
    minWidth: 180,
    suppressSizeToFit: true,
    resizable: true,
};

export const COLUMN_ACCOUNTS: SmartGridColDef = {
    ...getConnectionColumnConfig(DealConnectionType.ACCOUNT),
    headerName: 'Accounts',
    field: 'numOfAccounts',
    width: 80,
};

export const COLUMN_CAMPAIGNS: SmartGridColDef = {
    ...getConnectionColumnConfig(DealConnectionType.CAMPAIGN),
    headerName: 'Campaigns',
    field: 'numOfCampaigns',
    width: 85,
};

export const COLUMN_AD_GROUPS: SmartGridColDef = {
    ...getConnectionColumnConfig(DealConnectionType.ADGROUP),
    headerName: 'Ad Groups',
    field: 'numOfAdgroups',
    width: 80,
};

export const COLUMN_NOTES: SmartGridColDef = {
    headerName: 'Notes',
    field: 'description',
    minWidth: 90,
};

export const COLUMN_CREATED_BY: SmartGridColDef = {
    headerName: 'Created by',
    field: 'createdBy',
    minWidth: 180,
};

export const COLUMN_ACTIONS: SmartGridColDef = {
    headerName: '',
    cellRendererFramework: DealActionsCellComponent,
    pinned: 'right',
    width: 75,
    suppressSizeToFit: true,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};

function getConnectionColumnConfig(
    connectionType: DealConnectionType
): Partial<SmartGridColDef> {
    return {
        cellClassRules: {
            'zem-deals-grid__cell--clickable': canViewConnections,
        },
        onCellClicked: $event => openConnectionsModal(connectionType, $event),
        suppressSizeToFit: true,
        resizable: true,
    };
}

function canViewConnections(
    cellInfo: CellClassParams | CellClickedEvent
): boolean {
    return cellInfo.data.canViewConnections && cellInfo.value >= 1;
}

function openConnectionsModal(
    connectionType: DealConnectionType,
    cellInfo: CellClassParams | CellClickedEvent
) {
    if (canViewConnections(cellInfo)) {
        (<DealsView>cellInfo.context.componentParent).openConnectionsModal(
            cellInfo.data.id,
            connectionType
        );
    }
}
