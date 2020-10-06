import {ColDef} from 'ag-grid-community';
import {ConnectionActionsCellComponent} from '../../../../shared/components/connection-actions-cell/connection-actions-cell.component';
import {PublisherGroupConnectionLocation} from '../../../../core/publisher-groups/types/publisher-group-connection-location';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {LinkCellComponent} from '../../../../shared/components/smart-grid/components/cells/link-cell/link-cell.component';
import {LinkRendererParams} from '../../../../shared/components/smart-grid/components/cells/link-cell/types/link.renderer-params';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {LevelParam} from '../../../../app.constants';

export const PAGINATION_OPTIONS: PaginationOptions = {
    type: 'client',
    pageSizeOptions: [{name: '10', value: 10}],
    page: 1,
    pageSize: 10,
};

export const COLUMN_USED_ON: ColDef = {
    headerName: 'Used on',
    cellRendererFramework: LinkCellComponent,
    cellRendererParams: {
        getText: usedOnTextGetter,
        getLink: usedOnLinkGetter,
    } as LinkRendererParams<PublisherGroupConnection>,
};

export const COLUMN_USED_AS: ColDef = {
    headerName: 'Used as',
    valueGetter: usedAsGetter,
};

export const COLUMN_ACTIONS: ColDef = {
    headerName: '',
    width: 40,
    suppressSizeToFit: true,
    cellRendererFramework: ConnectionActionsCellComponent,
    pinned: 'right',
};

function usedOnTextGetter(item: PublisherGroupConnection): string {
    return `${CONNECTION_LOCATION_TO_ENTITY[item.location]}: ${item.name ||
        ''}`;
}

function usedOnLinkGetter(item: PublisherGroupConnection): string {
    const levelParam: LevelParam =
        CONNECTION_LOCATION_TO_LEVEL_PARAM[item.location];
    if (isDefined(levelParam)) {
        return `/v2/analytics/${levelParam}/${item.id}`;
    } else {
        return null;
    }
}

function usedAsGetter(params: {data: PublisherGroupConnection}): string {
    return CONNECTION_LOCATION_TO_ACTION[params?.data?.location];
}

const CONNECTION_LOCATION_TO_ENTITY: {
    [key in PublisherGroupConnectionLocation]:
        | 'Agency'
        | 'Account'
        | 'Campaign'
        | 'Ad group';
} = {
    agencyBlacklist: 'Agency',
    agencyWhitelist: 'Agency',
    accountBlacklist: 'Account',
    accountWhitelist: 'Account',
    campaignBlacklist: 'Campaign',
    campaignWhitelist: 'Campaign',
    adGroupBlacklist: 'Ad group',
    adGroupWhitelist: 'Ad group',
};

const CONNECTION_LOCATION_TO_LEVEL_PARAM: {
    [key in PublisherGroupConnectionLocation]: LevelParam;
} = {
    agencyBlacklist: null,
    agencyWhitelist: null,
    accountBlacklist: LevelParam.ACCOUNT,
    accountWhitelist: LevelParam.ACCOUNT,
    campaignBlacklist: LevelParam.CAMPAIGN,
    campaignWhitelist: LevelParam.CAMPAIGN,
    adGroupBlacklist: LevelParam.AD_GROUP,
    adGroupWhitelist: LevelParam.AD_GROUP,
};

const CONNECTION_LOCATION_TO_ACTION: {
    [key in PublisherGroupConnectionLocation]: 'Blacklist' | 'Whitelist';
} = {
    agencyBlacklist: 'Blacklist',
    agencyWhitelist: 'Whitelist',
    accountBlacklist: 'Blacklist',
    accountWhitelist: 'Whitelist',
    campaignBlacklist: 'Blacklist',
    campaignWhitelist: 'Whitelist',
    adGroupBlacklist: 'Blacklist',
    adGroupWhitelist: 'Whitelist',
};
