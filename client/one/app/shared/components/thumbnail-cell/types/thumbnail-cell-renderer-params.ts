import {ICellRendererParams} from 'ag-grid-community';
import {ThumbnailData} from './thumbnail-data';

export interface ThumbnailCellRendererParams extends ICellRendererParams {
    context: {
        componentParent: any;
    };
    data: ThumbnailData;
}
