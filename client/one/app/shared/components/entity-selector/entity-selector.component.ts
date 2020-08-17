import './entity-selector.component.less';

import {
    Input,
    OnChanges,
    Output,
    EventEmitter,
    Component,
    ChangeDetectionStrategy,
} from '@angular/core';
import {ENTITY_TYPE_TO_NAME} from './entity-selector.config';
import {EntitySelectorItem} from './types/entity-selector-item';
import {EntitySelectorItemsByType} from './types/entity-selector-items-by-type';
import * as arrayHelpers from '../../helpers/array.helpers';

@Component({
    selector: 'zem-entity-selector',
    templateUrl: './entity-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntitySelectorComponent implements OnChanges {
    @Input()
    selectedEntities: EntitySelectorItem[];
    @Input()
    availableEntities: EntitySelectorItem[];
    @Input()
    errors: string[];
    @Input()
    appendTo: 'body';
    @Output()
    searchEntities: EventEmitter<string> = new EventEmitter<string>();
    @Output()
    addEntity: EventEmitter<EntitySelectorItem> = new EventEmitter<
        EntitySelectorItem
    >();
    @Output()
    removeEntity: EventEmitter<EntitySelectorItem> = new EventEmitter<
        EntitySelectorItem
    >();
    @Output()
    open: EventEmitter<void> = new EventEmitter<void>();

    selectedGroupedEntities: EntitySelectorItemsByType[] = [];
    filteredAvailableEntities: EntitySelectorItem[];

    entityTypeNames = ENTITY_TYPE_TO_NAME;

    ngOnChanges(): void {
        this.selectedGroupedEntities = this.getGroupedEntities(
            this.selectedEntities
        );
        this.filteredAvailableEntities = this.getFilteredAvailableEntities(
            this.selectedEntities,
            this.availableEntities
        );
    }

    onSearchEntities(keyword: string): void {
        this.searchEntities.emit(keyword);
    }

    private getGroupedEntities(
        entities: EntitySelectorItem[]
    ): EntitySelectorItemsByType[] {
        return arrayHelpers
            .groupArray(entities, entity => entity.type)
            .map(group => ({type: group[0].type, entities: group}));
    }

    private getFilteredAvailableEntities(
        selectedEntities: EntitySelectorItem[],
        availableEntities: EntitySelectorItem[]
    ): EntitySelectorItem[] {
        const selectedEntitiesIds = selectedEntities.map(entity => entity.id);
        return availableEntities.filter(availableEntity => {
            return !selectedEntitiesIds.includes(availableEntity.id);
        });
    }
}
