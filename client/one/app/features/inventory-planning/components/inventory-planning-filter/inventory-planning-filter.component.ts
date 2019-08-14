import './inventory-planning-filter.component.less';

import {
    Component,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    ChangeDetectionStrategy,
    ViewChild,
    SimpleChanges,
} from '@angular/core';

import {Filters} from '../../types/filters';
import {FilterOption} from '../../types/filter-option';
import {DropdownDirective} from '../../../../shared/components/dropdown/dropdown.directive';
import {Category as CategorizedTagsListCategory} from '../../../../shared/components/categorized-tags-list/types/category';
import {Item as CategorizedTagsListItem} from '../../../../shared/components/categorized-tags-list/types/item';
import {Category as CategorizedSelectCategory} from '../../../../shared/components/categorized-select/types/category';
import {Item as CategorizedSelectItem} from '../../../../shared/components/categorized-select/types/item';
import {SelectionItem as CategorizedSelectSelectionItem} from '../../../../shared/components/categorized-select/types/selection-item';
import {BigNumberPipe} from '../../../../shared/pipes/big-number.pipe';

@Component({
    selector: 'zem-inventory-planning-filter',
    templateUrl: './inventory-planning-filter.component.html',
    providers: [BigNumberPipe],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningFilterComponent implements OnChanges {
    @Input()
    availableFilters: Filters;
    @Input()
    selectedFilters: Filters;
    @Output()
    onRemove = new EventEmitter<{key: string; value: string}>();
    @Output()
    onApply = new EventEmitter<{key: string; value: string}[]>();

    @ViewChild(DropdownDirective, {static: false})
    filterDropdown: DropdownDirective;

    categorizedOptions: CategorizedSelectCategory[];
    categorizedSelectedOptions: CategorizedTagsListCategory[];

    constructor(private bigNumberPipe: BigNumberPipe) {}

    ngOnChanges(changes: SimpleChanges) {
        this.categorizedOptions = this.getCategorizedOptions(
            this.availableFilters,
            this.selectedFilters
        );
        this.categorizedSelectedOptions = this.getCategorizedSelectedOptions(
            this.categorizedOptions
        );
    }

    removeSelected(removedOption: {
        category: CategorizedTagsListCategory;
        item: CategorizedTagsListItem;
    }): void {
        this.onRemove.emit({
            key: removedOption.category.key,
            value: removedOption.item.value,
        });
    }

    applyFilterSelection(selection: CategorizedSelectSelectionItem[]): void {
        const selectedFilters = selection.map(selectedFilter => {
            return {
                key: selectedFilter.categoryKey,
                value: selectedFilter.itemValue,
            };
        });
        this.onApply.emit(selectedFilters);
        this.filterDropdown.close();
    }

    private getCategorizedOptions(
        availableFilters: Filters,
        selectedFilters: Filters
    ): CategorizedSelectCategory[] {
        const categories: CategorizedSelectCategory[] = [];
        categories.push({
            name: 'Countries',
            key: 'countries',
            items: this.getFilterCategoryItems(
                availableFilters.countries,
                selectedFilters.countries
            ),
        });
        categories.push({
            name: 'Publishers',
            key: 'publishers',
            items: this.getFilterCategoryItems(
                availableFilters.publishers,
                selectedFilters.publishers
            ),
        });
        categories.push({
            name: 'Devices',
            key: 'devices',
            items: this.getFilterCategoryItems(
                availableFilters.devices,
                selectedFilters.devices
            ),
        });
        categories.push({
            name: 'Media Sources',
            key: 'sources',
            items: this.getFilterCategoryItems(
                availableFilters.sources,
                selectedFilters.sources
            ),
        });
        return categories;
    }

    private getFilterCategoryItems(
        availableItems: FilterOption[],
        selectedItems: FilterOption[]
    ): CategorizedSelectItem[] {
        const items: CategorizedSelectItem[] = [];
        const selectedItemsList: FilterOption[] = [];
        const unselectedItemsList: FilterOption[] = [];

        availableItems.forEach(availableItem => {
            for (const selectedItem of selectedItems) {
                if (selectedItem.value === availableItem.value) {
                    selectedItemsList.push(availableItem);
                    return;
                }
            }
            unselectedItemsList.push(availableItem);
        });

        // Include selected items first
        selectedItemsList.forEach(selectedItem => {
            items.push({
                name: selectedItem.name || selectedItem.value,
                value: selectedItem.value,
                description: this.bigNumberPipe.transform(
                    selectedItem.auctionCount
                ),
                selected: true,
            });
        });

        // Append unselected items after selected items
        unselectedItemsList.forEach(unselectedItem => {
            items.push({
                name: unselectedItem.name || unselectedItem.value,
                value: unselectedItem.value,
                description: this.bigNumberPipe.transform(
                    unselectedItem.auctionCount
                ),
                selected: false,
            });
        });

        return items;
    }

    private getCategorizedSelectedOptions(
        categories: CategorizedSelectCategory[]
    ): CategorizedTagsListCategory[] {
        const categoriesWithSelectedItems: CategorizedTagsListCategory[] = [];

        for (const category of categories) {
            const emptyCategory: CategorizedTagsListCategory = {
                ...category,
                items: [],
            };

            const selectedItems = category.items
                .filter(item => item.selected)
                .map(item => {
                    return {name: item.name, value: item.value};
                });
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
