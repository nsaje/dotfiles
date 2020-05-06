import './select-list.component.less';
import {
    Component,
    ChangeDetectionStrategy,
    Input,
    TemplateRef,
    Output,
    EventEmitter,
    OnChanges,
    ContentChild,
    SimpleChanges,
    AfterViewInit,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';

@Component({
    selector: 'zem-select-list',
    templateUrl: './select-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectListComponent implements OnChanges, AfterViewInit {
    @Input()
    selectedItems: any[];
    @Input()
    availableItems: any[];
    @Input('selectBindLabel')
    bindLabel: string;
    @Input('selectBindValue')
    bindValue: string;
    @Input('selectPlaceholder')
    placeholder: string;
    @Input('selectIsLoading')
    isLoading: boolean = false;
    @Input('selectSearchFn')
    searchFn: Function;
    @Input('selectGroupByValue')
    groupByValue: string;
    @Output()
    itemSelect = new EventEmitter<any>();
    @Output()
    search = new EventEmitter<string>();
    @Output()
    open = new EventEmitter<void>();

    @ContentChild('headerTemplate', {read: TemplateRef, static: false})
    headerTemplate: TemplateRef<any>;

    @ContentChild('emptyItemsTemplate', {read: TemplateRef, static: false})
    emptyItemsTemplate: TemplateRef<any>;

    @ContentChild('itemTemplate', {read: TemplateRef, static: false})
    itemTemplate: TemplateRef<any>;

    @ContentChild('selectItemTemplate', {read: TemplateRef, static: false})
    selectItemTemplate: TemplateRef<any>;

    @ContentChild('selectGroupTemplate', {read: TemplateRef, static: false})
    selectGroupTemplate: TemplateRef<any>;

    availableItemsFiltered: any[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.selectedItems || changes.availableItems) {
            this.availableItemsFiltered = this.availableItems.filter(x => {
                return this.selectedItems.every(
                    y => y[this.bindValue] !== x[this.bindValue]
                );
            });
        }
    }

    ngAfterViewInit(): void {
        if (!commonHelpers.isDefined(this.itemTemplate)) {
            throw new Error('ItemTemplate not provided!');
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    onItemSelect($event: any) {
        if (!commonHelpers.isDefined($event)) {
            return;
        }
        const item = this.availableItemsFiltered.filter(
            item => item[this.bindValue] === $event
        )[0];
        this.itemSelect.emit(item);
    }

    onSearch($event: string) {
        this.search.emit($event);
    }
}
