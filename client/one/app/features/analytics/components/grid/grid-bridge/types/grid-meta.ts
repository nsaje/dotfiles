import {PaginationOptions} from '../../../../../../shared/components/smart-grid/types/pagination-options';
import {GridRenderingEngineType} from '../../../../analytics.constants';
import {GridMetaData} from './grid-meta-data';

// meta information and functionality
export interface GridMeta {
    initialized: boolean; // meta-data initialized (true, false)
    loading: boolean; // stats data loading (true/false)
    renderingEngine: GridRenderingEngineType;
    paginationOptions: PaginationOptions;
    options: any; // Options (enableSelection, maxSelectedRows, etc.)
    api: any; // zemGridApi - api for exposed/public zem-grid functionality
    dataService: any; // zemGridDataService - access to data
    columnsService: any; // zemGridColumnsService
    orderService: any; // zemGridOrderService
    collapseService: any; // zemGridCollapseService
    selectionService: any; // zemGridSelectionService
    pubsub: any; // zemGridPubSub - internal message queue
    data: GridMetaData; // meta-data retrieved through Endpoint - columns definitions
    scope: any; // zem-grid scope used for running $digest and $emit internally
}
