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

@Component({
    selector: 'zem-list-group',
    templateUrl: './list-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListGroupComponent implements OnChanges {
    @Input()
    items: ListGroupItem[];
    @Input()
    value: string;
    @Input()
    isIconVisible: boolean = true;
    @Input()
    isDisplayValueVisible: boolean = true;
    @Output()
    valueChange = new EventEmitter<string>();

    filteredItems: ListGroupItem[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.items) {
            this.filteredItems = (this.items || []).filter(item =>
                item.isVisible()
            );
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }
}
