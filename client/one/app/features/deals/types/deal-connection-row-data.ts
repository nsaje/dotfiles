import {DealConnectionEntity} from '../../../core/deals/types/deal-connection-entity';

export interface DealConnectionRowData extends DealConnectionEntity {
    connectionId: string;
    connectionType: string;
}
