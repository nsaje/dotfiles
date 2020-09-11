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
import * as arrayHelpers from '../../helpers/array.helpers';

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
    @Input('selectIsDisabled')
    isDisabled: boolean = false;
    @Input('selectSearchFn')
    searchFn: Function;
    @Input()
    selectGroupByValue: string;
    @Input()
    groupByValue: string;
    @Input()
    itemListLimit: number;
    @Input()
    itemListLimitByGroup: {[key: string]: number};
    @Input()
    appendTo: 'body';
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

    @ContentChild('itemGroupTitleTemplate', {
        read: TemplateRef,
        static: false,
    })
    itemGroupTitleTemplate: TemplateRef<any>;

    @ContentChild('itemGroupFooterTemplate', {read: TemplateRef, static: false})
    itemGroupFooterTemplate: TemplateRef<any>;

    @ContentChild('selectItemTemplate', {read: TemplateRef, static: false})
    selectItemTemplate: TemplateRef<any>;

    @ContentChild('selectGroupTitleTemplate', {
        read: TemplateRef,
        static: false,
    })
    selectGroupTitleTemplate: TemplateRef<any>;

    @ContentChild('footerTemplate', {read: TemplateRef, static: false})
    footerTemplate: TemplateRef<any>;

    availableItemsFiltered: any[] = [];

    selectedItemsLimited: any[] = [];

    selectedItemsGroupedLimited: {
        groupName: string;
        items: any[];
        limitedItems: any[];
    }[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.selectedItems || changes.availableItems) {
            this.availableItemsFiltered = this.availableItems.filter(x => {
                return this.selectedItems.every(
                    y => y[this.bindValue] !== x[this.bindValue]
                );
            });
        }

        if (
            this.groupByValue &&
            (changes.selectedItems ||
                changes.itemListLimit ||
                changes.itemListLimitByGroup)
        ) {
            this.selectedItemsGroupedLimited = this.getGroupedLimitedItems(
                this.groupByValue,
                this.selectedItems,
                this.itemListLimitByGroup
                    ? this.itemListLimitByGroup
                    : this.itemListLimit
            );
        } else if (changes.selectedItems || changes.itemListLimit) {
            this.selectedItemsLimited = this.getLimitedItems(
                this.selectedItems,
                this.itemListLimit
            );
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

    private getGroupedLimitedItems(
        groupByValue: string,
        items: any[],
        itemListLimit: {[key: string]: number} | number
    ): {
        groupName: string;
        items: any[];
        limitedItems: any[];
    }[] {
        return arrayHelpers
            .groupArray(items, item => item[groupByValue])
            .map(group => ({
                groupName: group[0][groupByValue],
                items: group,
                limitedItems: this.getLimitedItems(
                    group,
                    itemListLimit instanceof Object
                        ? itemListLimit[group[0][groupByValue]]
                        : itemListLimit
                ),
            }));
    }

    private getLimitedItems(items: any[], itemListLimit: number): any[] {
        if (!commonHelpers.isDefined(itemListLimit)) {
            return items;
        }

        return items.slice(0, itemListLimit);
    }
}
