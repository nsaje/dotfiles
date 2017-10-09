import {Observable} from 'rxjs/Observable';
import {TestBed, inject} from '@angular/core/testing';
import {HttpClientModule} from '@angular/common/http';
import 'rxjs/add/observable/of';

import {InventoryPlanningStore} from './inventory-planning.store';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';

describe('InventoryPlanningStore', () => {
    let store: InventoryPlanningStore;

    const availableCountries = [
        {
            value: 'test country 1',
            name: 'Test country 1',
            auctionCount: 1000,
        },
        {
            value: 'test country 2',
            name: 'Test country 2',
            auctionCount: 2000,
        },
    ];
    const availablePublishers = [
        {
            value: 'test publisher 1',
            name: 'Test publisher 1',
            auctionCount: 100,
        },
        {
            value: 'test publisher 2',
            name: 'Test publisher 2',
            auctionCount: 200,
        },
    ];
    const availableDevices = [
        {
            value: 'test device 1',
            name: 'Test device 1',
            auctionCount: 10000,
        },
        {
            value: 'test device 2',
            name: 'Test device 2',
            auctionCount: 20000,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientModule],
            providers: [
                InventoryPlanningEndpoint,
            ],
        });
    });
    beforeEach(inject([InventoryPlanningEndpoint], (endpoint: InventoryPlanningEndpoint) => {
        spyOn(endpoint, 'loadSummary').and.returnValue(Observable.of({auctionCount: 100000, avgCpm: 2, winRatio: 0.5}));
        spyOn(endpoint, 'loadCountries').and.returnValue(Observable.of(availableCountries));
        spyOn(endpoint, 'loadPublishers').and.returnValue(Observable.of(availablePublishers));
        spyOn(endpoint, 'loadDevices').and.returnValue(Observable.of(availableDevices));

        store = new InventoryPlanningStore(endpoint);
    }));

    it('should correctly refresh data on init', () => {
        expect(store.state).toEqual({
            requests: {
                summary: {
                    inProgress: false,
                },
                countries: {
                    inProgress: false,
                },
                publishers: {
                    inProgress: false,
                },
                devices: {
                    inProgress: false,
                },
            },
            inventory: {auctionCount: 100000, avgCpm: 2, winRatio: 0.5},
            availableFilters: {
                countries: availableCountries,
                publishers: availablePublishers,
                devices: availableDevices,
            },
            selectedFilters: {
                countries: [],
                publishers: [],
                devices: [],
            },
        });
    });

    it('should correctly toggle countries', () => {
        store.toggleCountry('test country 1');
        expect(store.state.selectedFilters.countries).toEqual([{value: 'test country 1', name: 'Test country 1'}]);
        store.toggleCountry('test country 2');
        expect(store.state.selectedFilters.countries).toEqual([
            {value: 'test country 1', name: 'Test country 1'},
            {value: 'test country 2', name: 'Test country 2'},
        ]);
        store.toggleCountry('test country 1');
        expect(store.state.selectedFilters.countries).toEqual([{value: 'test country 2', name: 'Test country 2'}]);
    });

    it('should correctly toggle publishers', () => {
        store.togglePublisher('test publisher 1');
        expect(store.state.selectedFilters.publishers).toEqual([{value: 'test publisher 1', name: 'Test publisher 1'}]);
        store.togglePublisher('test publisher 2');
        expect(store.state.selectedFilters.publishers).toEqual([
            {value: 'test publisher 1', name: 'Test publisher 1'},
            {value: 'test publisher 2', name: 'Test publisher 2'},
        ]);
        store.togglePublisher('test publisher 1');
        expect(store.state.selectedFilters.publishers).toEqual([{value: 'test publisher 2', name: 'Test publisher 2'}]);
    });

    it('should correctly toggle devices', () => {
        store.toggleDevice('test device 1');
        expect(store.state.selectedFilters.devices).toEqual([{value: 'test device 1', name: 'Test device 1'}]);
        store.toggleDevice('test device 2');
        expect(store.state.selectedFilters.devices).toEqual([
            {value: 'test device 1', name: 'Test device 1'},
            {value: 'test device 2', name: 'Test device 2'},
        ]);
        store.toggleDevice('test device 1');
        expect(store.state.selectedFilters.devices).toEqual([{value: 'test device 2', name: 'Test device 2'}]);
    });

    it('should correctly remove selected option', () => {
        store.toggleCountry('test country 1');
        expect(store.state.selectedFilters.countries).toEqual([{value: 'test country 1', name: 'Test country 1'}]);
        store.removeOption({key: 'countries', value: 'test country 1'});
        expect(store.state.selectedFilters.countries).toEqual([]);

        store.togglePublisher('test publisher 1');
        expect(store.state.selectedFilters.publishers).toEqual([{value: 'test publisher 1', name: 'Test publisher 1'}]);
        store.removeOption({key: 'publishers', value: 'test publisher 1'});
        expect(store.state.selectedFilters.publishers).toEqual([]);

        store.toggleDevice('test device 1');
        expect(store.state.selectedFilters.devices).toEqual([{value: 'test device 1', name: 'Test device 1'}]);
        store.removeOption({key: 'devices', value: 'test device 1'});
        expect(store.state.selectedFilters.devices).toEqual([]);
    });
});
