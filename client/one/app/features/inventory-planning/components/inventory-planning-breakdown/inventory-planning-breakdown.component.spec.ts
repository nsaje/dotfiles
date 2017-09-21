import {SimpleChange} from '@angular/core';
import {TestBed, ComponentFixture, async, fakeAsync, tick} from '@angular/core/testing';
import {InventoryPlanningBreakdownComponent} from './inventory-planning-breakdown.component';

describe('InventoryPlanningBreakdownComponent', () => {
    const testOption1 = {
        value: '1',
        name: 'Option 1',
        auctionCount: 10000,
    };
    const testOption2 = {
        value: '2',
        name: 'Option 2',
        auctionCount: 20000,
    };
    const testOption3 = {
        value: '3',
        name: 'Option 3',
        auctionCount: 30000,
    };

    let fixture: ComponentFixture<InventoryPlanningBreakdownComponent>;
    let component: InventoryPlanningBreakdownComponent;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [InventoryPlanningBreakdownComponent],
        })
        .compileComponents();

        fixture =  TestBed.createComponent(InventoryPlanningBreakdownComponent);
        component = fixture.componentInstance;
    }));

    it('should correctly search through available filter options', fakeAsync(() => {
        component.options = [testOption1, testOption2, testOption3];
        component.selected = [];
        component.ngOnInit();

        component.search$.next('');
        tick(500); // tslint:disable-line
        expect(component.searchResults).toEqual(component.options);

        component.search$.next('option');
        tick(500); // tslint:disable-line
        expect(component.searchResults).toEqual(component.options);

        component.search$.next('option 2');
        tick(500); // tslint:disable-line
        expect(component.searchResults).toEqual([testOption2]);

        component.search$.next('none');
        tick(500); // tslint:disable-line
        expect(component.searchResults).toEqual([]);
    }));

    it('should execute search with current search query when options update', () => {
        let changes: any;
        component.options = [];
        component.selected = [];
        component.searchQuery = '2';

        component.ngOnInit();

        component.options = [];
        changes = {
            options: new SimpleChange(null, component.options, false),
        };
        component.ngOnChanges(changes);
        expect(component.searchResults).toEqual([]);

        component.options = [testOption1];
        changes = {
            options: new SimpleChange(null, component.options, false),
        };
        component.ngOnChanges(changes);
        expect(component.searchResults).toEqual([]);

        component.options = [testOption1, testOption2];
        changes = {
            options: new SimpleChange(null, component.options, false),
        };
        component.ngOnChanges(changes);
        expect(component.searchResults).toEqual([testOption2]);
    });
});
