import './list-group-item.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {ListGroupItem} from '../../types/list-group-item';
import * as arrayHelpers from '../../../../helpers/array.helpers';

@Component({
    selector: 'zem-list-group-item',
    templateUrl: './list-group-item.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListGroupItemComponent implements OnChanges {
    @Input()
    item: ListGroupItem;
    @Input()
    selectedItemPath: string[];
    @Input()
    parentItemPath: string[];
    @Input()
    isIconVisible: boolean = true;
    @Input()
    isDisplayValueVisible: boolean = true;
    @Input()
    isParentExpanded: boolean = false;
    @Input()
    level: number;

    @Output()
    selectedItemPathChange = new EventEmitter<string[]>();

    isExpanded: boolean = false;
    isSelected: boolean = false;

    itemPath: string[];

    ngOnChanges(): void {
        this.itemPath = this.item.value
            ? [...this.parentItemPath, this.item.value]
            : [...this.parentItemPath];

        const hasSelectedSubItem = this.hasSelectedSubItem(
            this.item,
            this.itemPath,
            this.selectedItemPath
        );
        this.isExpanded = this.isParentExpanded && hasSelectedSubItem;
        this.isSelected = this.getIsSelected(
            this.item,
            this.itemPath,
            this.selectedItemPath,
            this.isDisplayValueVisible,
            this.level,
            hasSelectedSubItem
        );
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    toggleItem(): void {
        if (
            arrayHelpers.isEmpty(this.item.subItems) ||
            !this.isDisplayValueVisible
        ) {
            this.selectedItemPathChange.emit(this.itemPath);
        } else {
            this.isExpanded = !this.isExpanded;
        }
    }

    private hasSelectedSubItem(
        item: ListGroupItem,
        itemPath: string[],
        selectedItemPath: string[]
    ): boolean {
        if (arrayHelpers.isEqual(itemPath, selectedItemPath)) {
            return true;
        }

        if (!arrayHelpers.isEmpty(item.subItems)) {
            for (const subItem of item.subItems) {
                const isSelected = this.hasSelectedSubItem(
                    subItem,
                    [...itemPath, subItem.value],
                    selectedItemPath
                );
                if (isSelected) {
                    return true;
                }
            }
        }
        return false;
    }

    private getIsSelected(
        item: ListGroupItem,
        itemPath: string[],
        selectedItemPath: string[],
        isDisplayValueVisible: boolean,
        level: number,
        hasSelectedSubItem: boolean
    ) {
        if (!isDisplayValueVisible) {
            return hasSelectedSubItem;
        } else if (level === 0) {
            return (
                arrayHelpers.isEqual(itemPath, selectedItemPath) &&
                arrayHelpers.isEmpty(item.subItems)
            );
        } else {
            return arrayHelpers.isEqual(itemPath, selectedItemPath);
        }
    }
}
