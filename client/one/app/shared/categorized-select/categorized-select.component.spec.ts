import {SimpleChanges, SimpleChange} from '@angular/core';
import {TestBed, ComponentFixture, async, fakeAsync, tick} from '@angular/core/testing';

import {CategorizedSelectComponent} from './categorized-select.component';
import {Category} from './types/category';
import {Item} from './types/item';
import {DEFAULT_CONFIG} from './categorized-select.constants';

describe('CategorizedSelectComponent', () => {
    const testItem1 = {
        value: '1',
        name: 'Item 1',
        description: 'Description 1',
        selected: true,
    };
    const testItem2 = {
        value: '2',
        name: 'Item 2',
        description: 'Description 2',
        selected: false,
    };
    const testItem3 = {
        value: '3',
        name: 'Item 3',
        description: 'Description 3',
        selected: true,
    };
    const testItem4 = {
        value: '4',
        name: 'Item 4',
        description: 'Description 4',
        selected: true,
    };
    const testCategory1 = {
        name: 'Category 1',
        key: 'category1',
        items: [testItem1, testItem2],
    };
    const testCategory2 = {
        name: 'Category 2',
        key: 'category2',
        items: [testItem3, testItem4],
    };

    let fixture: ComponentFixture<CategorizedSelectComponent>;
    let component: CategorizedSelectComponent;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [CategorizedSelectComponent],
        })
        .compileComponents();

        fixture =  TestBed.createComponent(CategorizedSelectComponent);
        component = fixture.componentInstance;
    }));

    it('should correctly select selected category', () => {
        component.categorizedItems = [testCategory1, testCategory2];
        component.ngOnInit();
        expect(component.selectedCategory).toEqual(null);

        component.selectCategory('category1');
        expect(component.selectedCategory).toEqual(testCategory1);

        component.selectCategory('category2');
        expect(component.selectedCategory).toEqual(testCategory2);

        component.selectCategory('unknownCategory');
        expect(component.selectedCategory).toEqual(testCategory2);
    });

    it('should correctly reset selected category', () => {
        component.categorizedItems = [testCategory1, testCategory2];
        component.selectCategory('category1');
        component.highlightedEntity = testItem1;
        component.searchQuery = 'Item';
        component.ngOnInit();

        expect(component.renderedItems).toEqual(testCategory1.items);

        component.resetSelectedCategory();
        expect(component.selectedCategory).toEqual(null);
        expect(<Item | Category> component.highlightedEntity).toEqual(<Item | Category> testCategory1);
        expect(component.searchQuery).toEqual('');
        expect(component.renderedItems).toEqual([]);
    });

    it('should correctly update rendered items on search if category is selected', fakeAsync(() => {
        component.categorizedItems = [testCategory1, testCategory2];
        component.ngOnInit();

        component.selectCategory('category1');

        component.search$.next('');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual(testCategory1.items);

        component.search$.next();
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual(testCategory1.items);

        component.search$.next('Item');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual(testCategory1.items);

        component.search$.next('item 2');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual([testItem2]);

        component.search$.next('none');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual([]);

        component.selectCategory('category2');

        component.search$.next('Item 1');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual([]);

        component.search$.next('Item 3');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual([testItem3]);
    }));

    it('should not update rendered items on search if category is not selected', fakeAsync(() => {
        component.categorizedItems = [testCategory1, testCategory2];
        component.ngOnInit();

        expect(component.renderedItems).toEqual([]);
        component.search$.next('Item');
        tick(500); // tslint:disable-line
        expect(component.renderedItems).toEqual([]);
    }));


    it('should correctly set selected items when categorizedItems input changes', () => {
        let changes: SimpleChanges;
        component.ngOnInit();

        component.categorizedItems = [];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.selectedItems).toEqual([]);

        component.categorizedItems = [testCategory1];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.selectedItems).toEqual([{categoryKey: 'category1', itemValue: '1'}]);

        component.selectedItems = [{categoryKey: 'category1', itemValue: '2'}];
        component.unselectedItems = [{categoryKey: 'category2', itemValue: '4'}];
        component.categorizedItems = [testCategory1, testCategory2];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.selectedItems).toEqual([
            {categoryKey: 'category1', itemValue: '1'},
            {categoryKey: 'category1', itemValue: '2'},
            {categoryKey: 'category2', itemValue: '3'},
        ]);
    });

    it('should keep currently selected category selected when categorizedItems input changes', () => {
        let changes: SimpleChanges;
        component.ngOnInit();

        component.categorizedItems = [testCategory1];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.selectedCategory).toEqual(null);

        component.selectCategory('category1');
        expect(component.selectedCategory).toEqual(testCategory1);

        component.categorizedItems = [testCategory1, testCategory2];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.selectedCategory).toEqual(testCategory1);
    });

    it('should correctly update rendered items when categorizedItems input changes', () => {
        let changes: SimpleChanges;
        component.ngOnInit();
        component.selectedCategory = testCategory1;

        component.categorizedItems = [];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.renderedItems).toEqual([]);

        component.categorizedItems = [testCategory1];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.renderedItems).toEqual(testCategory1.items);

        component.searchQuery = 'Item 2';
        component.categorizedItems = [testCategory1, testCategory2];
        changes = {
            categorizedItems: new SimpleChange(null, component.categorizedItems, false),
        };
        component.ngOnChanges(changes);
        expect(component.renderedItems).toEqual([testItem2]);
    });

    it('should correctly toggle items', () => {
        component.ngOnInit();
        component.selectedItems = [{categoryKey: 'category1', itemValue: '1'}];
        component.unselectedItems = [{categoryKey: 'category2', itemValue: '3'}];

        component.selectedCategory = testCategory1;
        component.toggleItem(testItem1);
        expect(component.selectedItems).toEqual([]);
        expect(component.unselectedItems).toEqual([
            {categoryKey: 'category2', itemValue: '3'},
            {categoryKey: 'category1', itemValue: '1'},
        ]);

        component.toggleItem(testItem2);
        expect(component.selectedItems).toEqual([
            {categoryKey: 'category1', itemValue: '2'},
        ]);
        expect(component.unselectedItems).toEqual([
            {categoryKey: 'category2', itemValue: '3'},
            {categoryKey: 'category1', itemValue: '1'},
        ]);

        component.selectedCategory = testCategory2;
        component.toggleItem(testItem3);
        expect(component.selectedItems).toEqual([
            {categoryKey: 'category1', itemValue: '2'},
            {categoryKey: 'category2', itemValue: '3'},
        ]);
        expect(component.unselectedItems).toEqual([
            {categoryKey: 'category1', itemValue: '1'},
        ]);
    });

    it('should correctly update config when config input changes', () => {
        let changes: SimpleChanges;
        component.ngOnInit();
        expect(component.config).toEqual(DEFAULT_CONFIG);

        component.configOverride = {
            enableKeyBindings: true,
        };
        changes = {
            configOverride: new SimpleChange(null, component.configOverride, false),
        };
        component.ngOnChanges(changes);
        expect(component.config).toEqual({
            ...DEFAULT_CONFIG,
            enableKeyBindings: true,
        });
    });
});
