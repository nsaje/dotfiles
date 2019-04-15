import {EntityType, EntityUpdateAction} from '../../../app.constants';

export interface EntityUpdate {
    id: string;
    type: EntityType;
    action: EntityUpdateAction;
}
