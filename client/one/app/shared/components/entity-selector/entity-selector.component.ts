import './entity-selector.component.less';

import {
    Input,
    Output,
    EventEmitter,
    Component,
    ChangeDetectionStrategy,
} from '@angular/core';
import {ENTITY_TYPE_TO_NAME} from './entity-selector.config';
import {EntitySelectorItem} from './types/entity-selector-item';

@Component({
    selector: 'zem-entity-selector',
    templateUrl: './entity-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntitySelectorComponent {
    @Input()
    selectedEntities: EntitySelectorItem[] = [];
    @Input()
    availableEntities: EntitySelectorItem[] = [];
    @Input()
    errors: string[];
    @Input()
    appendTo: 'body';
    @Input()
    isDisabled: boolean = false;
    @Input()
    groupByValue: string = 'type';
    @Input()
    selectPlaceholder: string = 'Add account, campaign, ad group';
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

    entityTypeNames = ENTITY_TYPE_TO_NAME;
}
