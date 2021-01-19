import {ICellRendererParams} from 'ag-grid-community';
import {Creative} from '../../../../core/creatives/types/creative';
import {CreativesComponent} from '../components/creatives/creatives.component';

export interface CreativeRendererParams extends ICellRendererParams {
    context: {
        componentParent: CreativesComponent;
    };
    data: Creative;
}
