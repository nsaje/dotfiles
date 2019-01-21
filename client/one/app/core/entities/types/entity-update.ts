import {EntityType, EntityUpdateAction} from '../../../app.constants';

export interface EntityUpdate {
    id: number;
    type: EntityType;
    action: EntityUpdateAction;
}
