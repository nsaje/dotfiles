import {Deal} from '../../../core/deals/types/deal';

export interface FormattedDeal extends Deal {
    canViewConnections: boolean;
}
