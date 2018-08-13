import {SimpleChanges, SimpleChange} from '@angular/core';
import {TestBed, ComponentFixture, async} from '@angular/core/testing';

import {SharedModule} from '../../../../shared/shared.module';
import {InventoryPlanningFilterComponent} from './inventory-planning-filter.component';

describe('InventoryPlanningFilterComponent', () => {
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
    const testOption4 = {
        value: '4',
        name: 'Option 4',
        auctionCount: 40000,
    };
    const testOption5 = {
        value: '5',
        name: 'Option 5',
        auctionCount: 50000,
    };

    let fixture: ComponentFixture<InventoryPlanningFilterComponent>;
    let component: InventoryPlanningFilterComponent;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            imports: [SharedModule],
            declarations: [InventoryPlanningFilterComponent],
        }).compileComponents();

        fixture = TestBed.createComponent(InventoryPlanningFilterComponent);
        component = fixture.componentInstance;
    }));

    it('should correctly generate categorizedOptions and categorizedSelectedOptions on inputs changes', () => {
        let changes: SimpleChanges;
        component.availableFilters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };
        component.selectedFilters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };
        changes = {
            availableFilters: new SimpleChange(
                null,
                component.availableFilters,
                false
            ),
            selectedFilters: new SimpleChange(
                null,
                component.selectedFilters,
                false
            ),
        };
        component.ngOnChanges(changes);
        expect(component.categorizedOptions).toEqual([
            {name: 'Countries', key: 'countries', items: []},
            {name: 'Publishers', key: 'publishers', items: []},
            {name: 'Devices', key: 'devices', items: []},
            {name: 'Media Sources', key: 'sources', items: []},
        ]);
        expect(component.categorizedSelectedOptions).toEqual([]);

        component.availableFilters = {
            countries: [testOption1, testOption2],
            publishers: [testOption3],
            devices: [testOption4],
            sources: [testOption5],
        };
        component.selectedFilters = {
            countries: [testOption2],
            publishers: [testOption3],
            devices: [],
            sources: [],
        };
        changes = {
            availableFilters: new SimpleChange(
                null,
                component.availableFilters,
                false
            ),
            selectedFilters: new SimpleChange(
                null,
                component.selectedFilters,
                false
            ),
        };
        component.ngOnChanges(changes);
        expect(component.categorizedOptions).toEqual([
            {
                name: 'Countries',
                key: 'countries',
                items: [
                    // NOTE: Selected options must be included first
                    {
                        name: 'Option 2',
                        value: '2',
                        description: '20 K',
                        selected: true,
                    },
                    {
                        name: 'Option 1',
                        value: '1',
                        description: '10 K',
                        selected: false,
                    },
                ],
            },
            {
                name: 'Publishers',
                key: 'publishers',
                items: [
                    {
                        name: 'Option 3',
                        value: '3',
                        description: '30 K',
                        selected: true,
                    },
                ],
            },
            {
                name: 'Devices',
                key: 'devices',
                items: [
                    {
                        name: 'Option 4',
                        value: '4',
                        description: '40 K',
                        selected: false,
                    },
                ],
            },
            {
                name: 'Media Sources',
                key: 'sources',
                items: [
                    {
                        name: 'Option 5',
                        value: '5',
                        description: '50 K',
                        selected: false,
                    },
                ],
            },
        ]);
        expect(component.categorizedSelectedOptions).toEqual([
            {
                name: 'Countries',
                key: 'countries',
                items: [{name: 'Option 2', value: '2'}],
            },
            {
                name: 'Publishers',
                key: 'publishers',
                items: [{name: 'Option 3', value: '3'}],
            },
        ]);
    });
});
