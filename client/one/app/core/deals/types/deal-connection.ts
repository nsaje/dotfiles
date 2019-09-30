import {DealConnectionEntity} from './deal-connection-entity';

export interface DealConnection {
    id: string;
    account: DealConnectionEntity;
    campaign: DealConnectionEntity;
    adgroup: DealConnectionEntity;
}
