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
    @Output()
    itemSelected = new EventEmitter<any>();
    @Output()
    search = new EventEmitter<string>();

    @ContentChild('headerTemplate', {read: TemplateRef, static: false})
    headerTemplate: TemplateRef<any>;

    @ContentChild('emptyItemsTemplate', {read: TemplateRef, static: false})
    emptyItemsTemplate: TemplateRef<any>;

    @ContentChild('itemTemplate', {read: TemplateRef, static: false})
    itemTemplate: TemplateRef<any>;

    @ContentChild('selectItemTemplate', {read: TemplateRef, static: false})
    selectItemTemplate: TemplateRef<any>;

    availableItemsFiltered: any[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.items || changes.availableItems) {
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

    onItemSelected($event: any) {
        if (!commonHelpers.isDefined($event)) {
            return;
        }
        const item = this.availableItemsFiltered.filter(
            item => item[this.bindValue] === $event
        )[0];
        this.itemSelected.emit(item);
    }

    onSearch($event: string) {
        this.search.emit($event);
    }
}
