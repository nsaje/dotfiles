import {ICellRendererParams} from 'ag-grid-community';
import {CreditsView} from '../../../views/credits/credits.view';
import {Credit} from '../../../../../core/credits/types/credit';
import {CreditGridType} from '../../../credits.constants';

export interface CreditRendererParams extends ICellRendererParams {
    context: {
        componentParent: CreditsView;
    };
    data: Credit;
    creditGridType?: CreditGridType;
}
