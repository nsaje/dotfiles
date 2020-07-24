import {EntityType} from '../../../../app.constants';
import {EntitySelectorItem} from './entity-selector-item';

export interface EntitySelectorItemsByType {
    type: EntityType;
    entities: EntitySelectorItem[];
}
