import './categorized-select.component.less';

import {
    Component, Input, Output, EventEmitter, OnInit, OnChanges, OnDestroy, ChangeDetectionStrategy, ElementRef,
    ChangeDetectorRef, SimpleChanges
} from '@angular/core';
import {Subscription} from 'rxjs/Subscription';
import {Subject} from 'rxjs/Subject';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';

import {Config} from './types/config';
import {Category} from './types/category';
import {Item} from './types/item';
import {SelectionItem} from './types/selection-item';
import {DEFAULT_CONFIG} from './categorized-select.constants';

const RENDERED_ITEMS_COUNT = 100;
const SEARCH_DEBOUNCE_TIME = 200;
const KEY_ENTER = 13;
const KEY_SPACE = 32;
const KEY_LEFT_ARROW = 37;
const KEY_UP_ARROW = 38;
const KEY_RIGHT_ARROW = 39;
const KEY_DOWN_ARROW = 40;
const HANDLED_KEY_BINDINGS = [KEY_ENTER, KEY_SPACE, KEY_UP_ARROW, KEY_DOWN_ARROW, KEY_LEFT_ARROW, KEY_RIGHT_ARROW];

@Component({
    selector: 'zem-categorized-select',
    templateUrl: './categorized-select.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategorizedSelectComponent implements OnInit, OnChanges, OnDestroy {
    @Input() categorizedItems: Category[];
    @Input('config') configOverride?: Config;
    @Output() onApply = new EventEmitter<SelectionItem[]>();

    config: Config;
    selectedCategory: Category = null;
    selectedItems: SelectionItem[] = [];
    unselectedItems: SelectionItem[] = [];
    renderedItems: Item[] = [];
    highlightedEntity: Category | Item;
    searchQuery: string = '';
    search$: Subject<string> = new Subject<string>();

    private searchSubscription: Subscription;
    private keyBindingsEventHandler: (event: KeyboardEvent) => void;

    constructor (private elementRef: ElementRef, private changeDetectorRef: ChangeDetectorRef) {}

    ngOnInit () {
        this.searchSubscription = this.search$
            .pipe(
                debounceTime(SEARCH_DEBOUNCE_TIME),
                distinctUntilChanged()
            )
            .subscribe(searchQuery => {
                if (!this.selectedCategory) {
                    // User might have reset selected category before search executed. Ignore search in that case.
                    return;
                }
                this.searchQuery = searchQuery;
                this.renderedItems = this.getRenderedItems(this.selectedCategory, this.searchQuery);
                this.changeDetectorRef.detectChanges();
            });

        this.updateConfig(this.configOverride);
    }

    ngOnChanges (changes: SimpleChanges) {
        if (changes.categorizedItems) {
            this.categorizedItems = this.addCategoryKeyToItems(this.categorizedItems);
            this.selectedItems = this.getSelectedItems(this.categorizedItems, this.selectedItems, this.unselectedItems);
            this.unselectedItems = [];

            if (this.selectedCategory) {
                this.selectCategory(this.selectedCategory.key);
            }
        }

        if (changes.configOverride) {
            this.updateConfig(this.configOverride);
        }
    }

    ngOnDestroy () {
        this.searchSubscription.unsubscribe();
        this.disableKeyBindings();
    }

    applySelection (): void {
        this.onApply.emit(this.selectedItems);
    }

    selectCategory (key: string): void {
        const selectedCategory = (this.categorizedItems || []).filter((category: Category) => category.key === key)[0];
        if (!selectedCategory) {
            return;
        }

        this.renderedItems = this.getRenderedItems(selectedCategory, this.searchQuery);
        this.selectedCategory = selectedCategory;
        this.highlightedEntity = null;

        setTimeout(() => {
            const searchInput = this.elementRef.nativeElement.querySelector('input');
            if (searchInput) {
                searchInput.focus();
            }
        }, 0); // tslint:disable-line align
    }

    resetSelectedCategory (): void {
        this.highlightedEntity = this.selectedCategory;
        this.selectedCategory = null;
        this.searchQuery = '';
        this.renderedItems = [];
    }

    toggleItem (toggledItem: Item): void {
        if (this.isItemInList(toggledItem, this.selectedItems)) {
            this.selectedItems = this.selectedItems.filter(selectedItem => {
                return selectedItem.categoryKey !== toggledItem.categoryKey ||
                       selectedItem.itemValue !== toggledItem.value;
            });
            this.unselectedItems = [
                ...this.unselectedItems,
                {categoryKey: toggledItem.categoryKey, itemValue: toggledItem.value},
            ];
        } else {
            this.unselectedItems = this.unselectedItems.filter(unselectedItem => {
                return unselectedItem.categoryKey !== toggledItem.categoryKey ||
                       unselectedItem.itemValue !== toggledItem.value;
            });
            this.selectedItems = [
                ...this.selectedItems,
                {categoryKey: toggledItem.categoryKey, itemValue: toggledItem.value},
            ];
        }
    }

    isItemInList (item: Item, list: SelectionItem[]): boolean {
        for (const listItem of list) {
            if (listItem.categoryKey === item.categoryKey && listItem.itemValue === item.value) {
                return true;
            }
        }
        return false;
    }

    private addCategoryKeyToItems (categorizedItems: Category[]): Category[] {
        return categorizedItems.map(category => {
            return {
                ...category,
                items: category.items.map(item => {
                    return {
                        ...item,
                        categoryKey: category.key,
                    };
                }),
            };
        });
    }

    private getSelectedItems (
        categorizedItems: Category[], selectedItems: SelectionItem[], unselectedItems: SelectionItem[]
    ): SelectionItem[] {
        const mergedSelectedItems: SelectionItem[] = [];
        categorizedItems.forEach(category => {
            category.items.forEach(item => {
                let isItemSelected = false;
                if (item.selected && !this.isItemInList(item, this.unselectedItems)) {
                    isItemSelected = true;
                } else if (!item.selected && this.isItemInList(item, this.selectedItems)) {
                    isItemSelected = true;
                }
                if (isItemSelected) {
                    mergedSelectedItems.push({categoryKey: category.key, itemValue: item.value});
                }
            });
        });
        return mergedSelectedItems;
    }

    private getRenderedItems (selectedCategory: Category, searchQuery: string): Item[] {
        let searchResults: Item[] = [];

        if (!searchQuery || searchQuery === '') {
            searchResults = selectedCategory.items;
        } else {
            searchQuery = searchQuery.toLowerCase();
            searchResults = selectedCategory.items.filter(item => {
                const itemName = item.name || '';
                return itemName.toLowerCase().indexOf(searchQuery) !== -1;
            });
        }

        return searchResults.slice(0, RENDERED_ITEMS_COUNT);
    }

    private updateConfig (configOverride?: Config): void {
        this.config = {
            ...DEFAULT_CONFIG,
            ...this.configOverride,
        };

        this.disableKeyBindings();
        if (this.config.enableKeyBindings) {
            this.enableKeyBindings();
        }
    }

    private handleKeyBindings (event: KeyboardEvent): void {
        if (HANDLED_KEY_BINDINGS.indexOf(event.keyCode) === -1) {
            return;
        }

        if (event.keyCode === KEY_UP_ARROW || event.keyCode === KEY_DOWN_ARROW) {
            this.handleUpAndDownKeys(event);
        } else if (event.keyCode === KEY_RIGHT_ARROW) {
            this.handleRightKey(event);
        } else if (event.keyCode === KEY_LEFT_ARROW) {
            this.handleLeftKey(event);
        } else if (event.keyCode === KEY_SPACE) {
            this.handleSpaceKey(event);
        } else if (event.keyCode === KEY_ENTER) {
            this.handleEnterKey(event);
        }

        this.changeDetectorRef.detectChanges();
    }

    private handleUpAndDownKeys (event: KeyboardEvent): void {
        event.preventDefault();
        event.stopPropagation();

        let maxIndex = 0;
        let highlightedIndex = -1;
        let collection: any = [];
        if (this.selectedCategory) {
            collection = this.renderedItems;
        } else {
            collection = this.categorizedItems;
        }

        maxIndex = collection.length - 1;
        highlightedIndex = collection.indexOf(this.highlightedEntity);

        if (event.keyCode === KEY_UP_ARROW) {
            highlightedIndex = (highlightedIndex <= 0 ? maxIndex : --highlightedIndex);
        } else if (event.keyCode === KEY_DOWN_ARROW) {
            highlightedIndex = (highlightedIndex >= maxIndex ? 0 : ++highlightedIndex);
        }

        this.highlightedEntity = collection[highlightedIndex];
        this.scrollToIndex(highlightedIndex);
    }

    private handleRightKey (event: KeyboardEvent): void {
        if (this.selectedCategory || this.categorizedItems.indexOf(<Category> this.highlightedEntity) === -1) {
            return;
        }
        this.selectCategory((<Category> this.highlightedEntity).key);
        event.preventDefault();
        event.stopPropagation();
    }

    private handleLeftKey (event: KeyboardEvent): void {
        if (!this.selectedCategory) {
            return;
        }
        this.resetSelectedCategory();
        event.preventDefault();
        event.stopPropagation();
    }

    private handleSpaceKey (event: KeyboardEvent): void {
        if (!this.selectedCategory || this.renderedItems.indexOf(<Item> this.highlightedEntity) === -1) {
            return;
        }
        this.toggleItem(<Item> this.highlightedEntity);
        event.preventDefault();
        event.stopPropagation();
    }

    private handleEnterKey (event: KeyboardEvent): void {
        this.applySelection();
        event.preventDefault();
        event.stopPropagation();
    }

    private scrollToIndex (index: number): void {
        const scrollContainer: HTMLElement =
            this.elementRef.nativeElement.querySelector('.zem-categorized-select__lists-container');
        const listItem: HTMLElement =
            this.elementRef.nativeElement.querySelectorAll('.zem-categorized-select__list-item')[index];

        if (!scrollContainer || !listItem) {
            return;
        }

        const scrollContainerStyle = getComputedStyle(scrollContainer);
        const scrollContainerPaddings =
            parseInt(scrollContainerStyle.paddingTop, 10) +  parseInt(scrollContainerStyle.paddingBottom, 10); // tslint:disable-line no-magic-numbers max-line-length
        const scrollContainerHeight = scrollContainer.offsetHeight - scrollContainerPaddings;
        const listItemStyle = getComputedStyle(listItem);
        const listItemMargins = parseInt(listItemStyle.marginTop, 10) + parseInt(listItemStyle.marginBottom, 10); // tslint:disable-line no-magic-numbers max-line-length
        const listItemHeight = listItem.offsetHeight + listItemMargins;
        const viewFrom = scrollContainer.scrollTop;
        const viewTo = viewFrom + scrollContainerHeight;
        const selectedPosition = index * listItemHeight;

        if (selectedPosition < viewFrom) {
            scrollContainer.scrollTop = selectedPosition;
        } else if (selectedPosition + listItemHeight >= viewTo) {
            scrollContainer.scrollTop = selectedPosition - scrollContainerHeight + listItemHeight;
        }
    }

    private enableKeyBindings (): void {
        document.addEventListener('keydown', this.keyBindingsEventHandler = this.handleKeyBindings.bind(this), true);
    }

    private disableKeyBindings (): void {
        document.removeEventListener('keydown', this.keyBindingsEventHandler, true);
    }
}
