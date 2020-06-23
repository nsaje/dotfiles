import './list-group-item.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ListGroupItem} from '../../types/list-group-item';
import {isEmpty} from '../../../../helpers/array.helpers';

@Component({
    selector: 'zem-list-group-item',
    templateUrl: './list-group-item.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListGroupItemComponent implements OnChanges {
    @Input()
    item: ListGroupItem;
    @Input()
    value: string;
    @Input()
    isIconVisible: boolean = true;
    @Input()
    isDisplayValueVisible: boolean = true;
    @Input()
    isParentExpanded: boolean = false;
    @Input()
    level: number;

    @Output()
    valueChange = new EventEmitter<string>();

    isExpanded: boolean = false;
    isSelected: boolean = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (
            (changes.isParentExpanded || changes.value) &&
            !isEmpty(this.item.subItems)
        ) {
            this.isExpanded =
                this.isParentExpanded &&
                this.setExpanded(this.item, this.value);
        }
        this.isSelected =
            this.item.value === this.value ||
            (this.isExpanded && !this.isDisplayValueVisible);
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    toggleItem(): void {
        if (isEmpty(this.item.subItems) || !this.isDisplayValueVisible) {
            this.valueChange.emit(this.item.value);
        } else {
            this.isExpanded = !this.isExpanded;
        }
    }

    private setExpanded(item: ListGroupItem, selectedValue: string): boolean {
        if (item.value === selectedValue) {
            return true;
        }

        let isExpanded = false;
        if (!isEmpty(item.subItems)) {
            for (const subItem of item.subItems) {
                isExpanded =
                    isExpanded || this.setExpanded(subItem, selectedValue);
            }
        }
        return isExpanded;
    }
}
