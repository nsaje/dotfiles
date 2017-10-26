import './inventory-planning-filter.component.less';

import {Component, Input, Output, EventEmitter, OnChanges, ChangeDetectionStrategy, ViewChild} from '@angular/core';

import {Filters} from '../types/filters';
import {FilterOption} from '../types/filter-option';
import {DropdownDirective} from '../../../shared/dropdown/dropdown.directive';
import {Category as CategorizedTagsListCategory} from '../../../shared/categorized-tags-list/types/category';
import {Item as CategorizedTagsListItem} from '../../../shared/categorized-tags-list/types/item';
import {Category as CategorizedSelectCategory} from '../../../shared/categorized-select/types/category';
import {Item as CategorizedSelectItem} from '../../../shared/categorized-select/types/item';
import {SelectionItem as CategorizedSelectSelectionItem} from '../../../shared/categorized-select/types/selection-item';
import {BigNumberPipe} from '../../../shared/big-number/big-number.pipe';

@Component({
    selector: 'zem-inventory-planning-filter',
    templateUrl: './inventory-planning-filter.component.html',
    providers: [BigNumberPipe],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningFilterComponent implements OnChanges {
    @Input() availableFilters: Filters;
    @Input() selectedFilters: Filters;
    @Output() onRemove = new EventEmitter<{key: string, value: string}>();
    @Output() onApply = new EventEmitter<{key: string, value: string}[]>();

    @ViewChild(DropdownDirective) filterDropdown: DropdownDirective;

    categorizedOptions: CategorizedSelectCategory[];
    categorizedSelectedOptions: CategorizedTagsListCategory[];

    constructor (private bigNumberPipe: BigNumberPipe) {}

    ngOnChanges (changes: any) {
        this.categorizedOptions = this.getCategorizedOptions(this.availableFilters, this.selectedFilters);
        this.categorizedSelectedOptions = this.getCategorizedSelectedOptions(this.categorizedOptions);
    }

    removeSelected ($event: {category: CategorizedTagsListCategory, item: CategorizedTagsListItem}): void {
        this.onRemove.emit({
            key: $event.category.key,
            value: $event.item.value,
        });
    }

    applyFilterSelection ($event: CategorizedSelectSelectionItem[]): void {
        const selectedFilters = $event.map(selectedFilter => {
            return {key: selectedFilter.categoryKey, value: selectedFilter.itemValue};
        });
        this.onApply.emit(selectedFilters);
        this.filterDropdown.close();
    }

    private getCategorizedOptions (
        availableFilters: Filters,
        selectedFilters: Filters
    ): CategorizedSelectCategory[] {
        const categories: CategorizedSelectCategory[] = [];
        categories.push({
            name: 'Countries',
            key: 'countries',
            items: this.getFilterCategoryItems(availableFilters.countries, selectedFilters.countries),
        });
        categories.push({
            name: 'Publishers',
            key: 'publishers',
            items: this.getFilterCategoryItems(availableFilters.publishers, selectedFilters.publishers),
        });
        categories.push({
            name: 'Devices',
            key: 'devices',
            items: this.getFilterCategoryItems(availableFilters.devices, selectedFilters.devices),
        });
        return categories;
    }

    private getFilterCategoryItems (
        availableItems: FilterOption[],
        selectedItems: FilterOption[]
    ): CategorizedSelectItem[] {
        const items: CategorizedSelectItem[] = [];

        // Include selected items first
        selectedItems.forEach(selectedItem => {
            items.push({
                name: selectedItem.name || selectedItem.value,
                value: selectedItem.value,
                description: this.bigNumberPipe.transform(selectedItem.auctionCount),
                selected: true,
            });
        });

        // Append unselected items after selected items
        const unselectedItems = availableItems.filter(availableItem => {
            for (const selectedItem of selectedItems) {
                if (selectedItem.value === availableItem.value) {
                    return false;
                }
            }
            return true;
        });
        unselectedItems.forEach(unselectedItem => {
            items.push({
                name: unselectedItem.name || unselectedItem.value,
                value: unselectedItem.value,
                description: this.bigNumberPipe.transform(unselectedItem.auctionCount),
                selected: false,
            });
        });

        return items;
    }

    private getCategorizedSelectedOptions (categories: CategorizedTagsListCategory[]): CategorizedTagsListCategory[] {
        const categoriesWithSelectedItems: CategorizedTagsListCategory[] = [];

        for (const category of categories) {
            const emptyCategory: CategorizedTagsListCategory = {
                ...category,
                items: [],
            };

            const selectedItems = category.items.filter(item => item.selected);
            if (selectedItems.length > 0) {
                categoriesWithSelectedItems.push({
                    ...emptyCategory,
                    items: selectedItems,
                });
            }
        }

        return categoriesWithSelectedItems;
    }
}
