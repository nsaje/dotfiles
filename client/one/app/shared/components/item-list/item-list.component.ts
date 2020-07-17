import './item-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    ContentChild,
    TemplateRef,
    Output,
    EventEmitter,
} from '@angular/core';

@Component({
    selector: 'zem-item-list',
    templateUrl: './item-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ItemListComponent<T> {
    @Input()
    items: T[] = [];
    @Input()
    selectedItems: T[] = [];
    @Input()
    multiple: boolean = false;
    @Input()
    canSelectNone: boolean = false;
    @Input()
    isDisabled: boolean = false;

    @Output()
    selectedItemsChange: EventEmitter<T[]> = new EventEmitter<T[]>();

    @ContentChild('itemTemplate', {read: TemplateRef, static: false})
    itemTemplate: TemplateRef<any>;
    @ContentChild('addItemTemplate', {read: TemplateRef, static: false})
    addItemTemplate: TemplateRef<any>;

    clickItem(event: MouseEvent, item: T) {
        const doMultiSelect: boolean =
            this.multiple && (event.shiftKey || event.ctrlKey);
        const itemAlreadySelected = this.selectedItems.includes(item);
        const onlyThisItemSelected: boolean =
            itemAlreadySelected && this.selectedItems.length === 1;

        if (itemAlreadySelected) {
            if (onlyThisItemSelected) {
                if (this.canSelectNone) {
                    this.selectedItemsChange.emit([]);
                }
                // else emit nothing, because selection hasn't changed
            } else {
                if (doMultiSelect) {
                    this.selectedItemsChange.emit(
                        this.selectedItems.filter(x => x !== item)
                    );
                } else {
                    this.selectedItemsChange.emit([item]);
                }
            }
        } else {
            if (doMultiSelect) {
                this.selectedItemsChange.emit([...this.selectedItems, item]);
            } else {
                this.selectedItemsChange.emit([item]);
            }
        }
    }
}
