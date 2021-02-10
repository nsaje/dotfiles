import {SmartGridColDef} from '../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {AdType, ViewportBreakpoint} from '../../../../../app.constants';
import {CheckboxCellComponent} from '../../../../../shared/components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {CheckboxRendererParams} from '../../../../../shared/components/smart-grid/components/cells/checkbox-cell/types/checkbox.renderer-params';
import {GridApi} from 'ag-grid-community';
import {CREATIVE_TYPES} from '../../creatives-shared.config';
import {ItemScopeCellComponent} from '../../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {Creative} from '../../../../../core/creatives/types/creative';
import {CreativeAssetCellComponent} from '../creative-asset-cell/creative-asset-cell.component';
import {CreativeActionsCellComponent} from '../creative-actions-cell/creative-actions-cell.component';
import {HeaderParams} from '../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {CreativeTagsCellComponent} from '../creative-tags-cell/creative-tags-cell.component';

const COLUMN_SELECT_ID = 'select';

export function refreshSelectColumn(gridApi: GridApi) {
    gridApi.refreshHeader();
    gridApi.refreshCells({
        columns: [COLUMN_SELECT_ID],
        force: true,
    });
}

function adTypeFormatter(params: {value: string}): string {
    return (
        CREATIVE_TYPES.find(type => type.id === AdType[params.value])?.name ||
        'N/A'
    );
}

export const COLUMN_SELECT: SmartGridColDef = {
    colId: COLUMN_SELECT_ID,
    headerName: '',
    cellRendererFramework: CheckboxCellComponent,
    cellRendererParams: {
        isChecked: (params: CheckboxRendererParams) => {
            return params.context.componentParent.store.isEntitySelected(
                params.data.id
            );
        },
        isDisabled: (params: CheckboxRendererParams) => false,
        setChecked: (value: boolean, params: CheckboxRendererParams) => {
            params.context.componentParent.store.setEntitySelected(
                params.data.id,
                value
            );
            refreshSelectColumn(params.api);
        },
    } as CheckboxRendererParams,
    headerComponentParams: {
        enableSelection: true,
        selectionOptions: {
            isChecked: (params: HeaderParams) => {
                return params.context.componentParent.store.areAllEntitiesSelected();
            },
            isDisabled: (params: HeaderParams) => false,
            setChecked: (value: boolean, params: HeaderParams) => {
                params.context.componentParent.store.setAllEntitiesSelected(
                    value
                );
                refreshSelectColumn(params.api);
            },
        },
    } as HeaderParams,
    pinned: 'left',
    minWidth: 32,
    maxWidth: 32,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};

export const COLUMN_TITLE: SmartGridColDef = {
    headerName: 'Title/Description',
    cellRendererFramework: CreativeAssetCellComponent,
    valueGetter: params => {
        return {
            imageUrl: params.data.imageUrl,
            title: params.data.title,
            description: params.data.description,
        };
    },
    width: 500,
    minWidth: 320,
    suppressSizeToFit: true,
    resizable: true,
    pinned: 'left',
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};

export const COLUMN_TAGS: SmartGridColDef = {
    headerName: 'Tags',
    field: 'tags',
    cellRendererFramework: CreativeTagsCellComponent,
    width: 80,
    minWidth: 80,
    resizable: true,
};

export const COLUMN_SCOPE: SmartGridColDef = {
    headerName: 'Scope',
    cellRendererFramework: ItemScopeCellComponent,
    valueGetter: params => {
        return {
            agencyId: params.data.agencyId,
            accountId: params.data.accountId,
        };
    },
    cellRendererParams: {
        getAgencyLink: item => {
            return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
        },
        getAccountLink: item => {
            return `/v2/analytics/account/${item.accountId}`;
        },
    } as ItemScopeRendererParams<Creative>,
    width: 200,
    minWidth: 200,
    resizable: true,
};

export const COLUMN_TYPE: SmartGridColDef = {
    headerName: 'Type',
    field: 'type',
    valueFormatter: adTypeFormatter,
    width: 80,
    minWidth: 80,
    resizable: true,
};

export const COLUMN_ACTIONS: SmartGridColDef = {
    headerName: '',
    cellRendererFramework: CreativeActionsCellComponent,
    pinned: 'right',
    maxWidth: 105,
    minWidth: 105,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
};
