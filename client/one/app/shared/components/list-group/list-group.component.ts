import './list-group.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ListGroupItem} from './types/list-group-item';
import {isEmpty} from '../../helpers/array.helpers';
import * as clone from 'clone';

@Component({
    selector: 'zem-list-group',
    templateUrl: './list-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListGroupComponent implements OnChanges {
    @Input()
    items: ListGroupItem[];
    @Input()
    rootPath: string[];
    @Input()
    selectedItemPath: string[];
    @Input()
    isIconVisible: boolean = true;
    @Input()
    isDisplayValueVisible: boolean = true;
    @Output()
    selectedItemPathChange = new EventEmitter<string[]>();

    filteredItems: ListGroupItem[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.items) {
            this.filteredItems = this.getFilteredItems(clone(this.items));
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    private getFilteredItems(items: ListGroupItem[]): ListGroupItem[] {
        const filteredItems: ListGroupItem[] = [];
        items.forEach(item => {
            if (item.isVisible()) {
                if (!isEmpty(item.subItems)) {
                    item.subItems = this.getFilteredItems(item.subItems);
                }
                filteredItems.push(item);
            }
        });
        return filteredItems;
    }
}
