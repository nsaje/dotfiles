import {CellClassParams, CellClickedEvent, ColDef} from 'ag-grid-community';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {Deal} from '../../../../core/deals/types/deal';
import {DealActionsCellComponent} from '../deal-actions-cell/deal-actions-cell.component';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {DealConnectionType} from '../../types/deal-connection-type';
import {DealsView} from '../../views/deals/deals.view';

export const COLUMN_ID: ColDef = {
    headerName: 'Id',
    field: 'id',
    width: 65,
    suppressSizeToFit: true,
};

export const COLUMN_DEAL_NAME: ColDef = {
    headerName: 'Deal name',
    field: 'name',
    minWidth: 240,
};

export const COLUMN_DEAL_ID: ColDef = {
    headerName: 'Deal Id',
    field: 'dealId',
    minWidth: 150,
};

export const COLUMN_SOURCE: ColDef = {
    headerName: 'Source',
    field: 'source',
    minWidth: 90,
};

export const COLUMN_FLOOR_PRICE: ColDef = {
    headerName: 'Floor price',
    field: 'floorPrice',
    width: 90,
    suppressSizeToFit: true,
};

export const COLUMN_VALID_FROM: ColDef = {
    headerName: 'Valid from',
    field: 'validFromDate',
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
    width: 110,
    suppressSizeToFit: true,
};

export const COLUMN_VALID_TO: ColDef = {
    headerName: 'Valid to',
    field: 'validToDate',
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
    width: 110,
    suppressSizeToFit: true,
};

export const COLUMN_SCOPE: ColDef = {
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
    resizable: true,
};

export const COLUMN_ACCOUNTS: ColDef = {
    ...getConnectionColumnConfig(DealConnectionType.ACCOUNT),
    headerName: 'Accounts',
    field: 'numOfAccounts',
    width: 70,
};

export const COLUMN_CAMPAIGNS: ColDef = {
    ...getConnectionColumnConfig(DealConnectionType.CAMPAIGN),
    headerName: 'Campaigns',
    field: 'numOfCampaigns',
    width: 80,
};

export const COLUMN_AD_GROUPS: ColDef = {
    ...getConnectionColumnConfig(DealConnectionType.ADGROUP),
    headerName: 'Ad Groups',
    field: 'numOfAdgroups',
    width: 80,
};

export const COLUMN_NOTES: ColDef = {
    headerName: 'Notes',
    field: 'description',
    minWidth: 90,
};

export const COLUMN_CREATED_BY: ColDef = {
    headerName: 'Created by',
    field: 'createdBy',
    minWidth: 180,
};

export const COLUMN_ACTIONS: ColDef = {
    headerName: '',
    cellRendererFramework: DealActionsCellComponent,
    pinned: 'right',
    width: 75,
    suppressSizeToFit: true,
};

function getConnectionColumnConfig(
    connectionType: DealConnectionType
): Partial<ColDef> {
    return {
        cellClassRules: {
            'zem-deals-grid__cell--clickable': canViewConnections,
        },
        onCellClicked: $event => openConnectionsModal(connectionType, $event),
        suppressSizeToFit: true,
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
