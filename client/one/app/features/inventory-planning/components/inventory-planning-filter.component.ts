import './inventory-planning-filter.component.less';

import {Component, Input, Output, EventEmitter, OnChanges, ChangeDetectionStrategy} from '@angular/core';

import {AvailableFilters} from '../types/available-filters';
import {AvailableFilterOption} from '../types/available-filter-option';
import {SelectedFilters} from '../types/selected-filters';
import {SelectedFilterOption} from '../types/selected-filter-option';
import {Category as CategorizedTagsListCategory} from '../../../shared/categorized-tags-list/types/category';
import {Item as CategorizedTagsListItem} from '../../../shared/categorized-tags-list/types/item';

@Component({
    selector: 'zem-inventory-planning-filter',
    templateUrl: './inventory-planning-filter.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningFilterComponent implements OnChanges {
    @Input() availableFilters: AvailableFilters;
    @Input() selectedFilters: SelectedFilters;
    @Output() onRemove = new EventEmitter<{key: string, value: string}>();
    @Output() onSelect = new EventEmitter<[{category: CategorizedTagsListCategory, item: CategorizedTagsListItem}]>();

    // FIXME (jurebajt): Substitute with CategorizedSelect Category type
    categorizedOptions: CategorizedTagsListCategory[];
    categorizedSelectedOptions: CategorizedTagsListCategory[];

    ngOnChanges (changes: any) {
        if (changes.selectedFilters) {
            this.categorizedOptions = this.getCategorizedOptions(this.availableFilters, this.selectedFilters);
            this.categorizedSelectedOptions = this.getCategorizedSelectedOptions(this.categorizedOptions);
        }
    }

    removeSelected ($event: {category: CategorizedTagsListCategory, item: CategorizedTagsListItem}): void {
        this.onRemove.emit({
            key: $event.category.key,
            value: $event.item.value,
        });
    }

    private getCategorizedOptions (
        availableFilters: AvailableFilters,
        selectedFilters: SelectedFilters
    ): CategorizedTagsListCategory[] {
        const categories: CategorizedTagsListCategory[] = [];
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
        availableItems: AvailableFilterOption[],
        selectedItems: SelectedFilterOption[]
    ): CategorizedTagsListItem[] {
        const items: CategorizedTagsListItem[] = [];

        // Include selected items first
        selectedItems.forEach(selectedItem => {
            items.push({
                name: selectedItem.name || selectedItem.value,
                value: selectedItem.value,
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
