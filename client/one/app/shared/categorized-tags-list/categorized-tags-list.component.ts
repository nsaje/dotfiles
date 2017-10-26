import './categorized-tags-list.component.less';

import {Component, Input, Output, EventEmitter, ChangeDetectionStrategy} from '@angular/core';

import {Category} from './types/category';
import {Item} from './types/item';

@Component({
    selector: 'zem-categorized-tags-list',
    templateUrl: './categorized-tags-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategorizedTagsListComponent {
    @Input() emptyText: string;
    @Input() categorizedItems: Category[];
    @Output() onRemove = new EventEmitter<{category: Category, item: Item}>();

    removeItem (category: Category, item: Item): void {
        this.onRemove.emit({category, item});
    }
}
