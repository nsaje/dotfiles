import {Observable} from 'rxjs/Observable';
import {TestBed, inject} from '@angular/core/testing';
import {HttpClientModule} from '@angular/common/http';
import 'rxjs/add/observable/of';
import 'rxjs/add/operator/delay';

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

    describe('with delayed mocked http requests', () => {
        beforeEach(inject([InventoryPlanningEndpoint], (endpoint: InventoryPlanningEndpoint) => {
            spyOn(endpoint, 'loadSummary').and.returnValue(
                Observable.of({auctionCount: 100000, avgCpm: 2, winRatio: 0.5}).delay(0)
            );
            spyOn(endpoint, 'loadCountries').and.returnValue(Observable.of(availableCountries).delay(0));
            spyOn(endpoint, 'loadPublishers').and.returnValue(Observable.of(availablePublishers).delay(0));
            spyOn(endpoint, 'loadDevices').and.returnValue(Observable.of(availableDevices).delay(0));

            store = new InventoryPlanningStore(endpoint);
        }));

        it('should correctly refresh data on init', done => {
            setTimeout(() => {
                expect(store.state).toEqual({
                    requests: {
                        summary: {
                            inProgress: false,
                            subscription: null,
                        },
                        countries: {
                            inProgress: false,
                            subscription: null,
                        },
                        publishers: {
                            inProgress: false,
                            subscription: null,
                        },
                        devices: {
                            inProgress: false,
                            subscription: null,
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
                done();
            }, 0); // tslint:disable-line align
        });
    });

    describe('without delayed mocked http requests', () => {
        beforeEach(inject([InventoryPlanningEndpoint], (endpoint: InventoryPlanningEndpoint) => {
            spyOn(endpoint, 'loadSummary').and.returnValue(
                Observable.of({auctionCount: 100000, avgCpm: 2, winRatio: 0.5})
            );
            spyOn(endpoint, 'loadCountries').and.returnValue(Observable.of(availableCountries));
            spyOn(endpoint, 'loadPublishers').and.returnValue(Observable.of(availablePublishers));
            spyOn(endpoint, 'loadDevices').and.returnValue(Observable.of(availableDevices));

            store = new InventoryPlanningStore(endpoint);
        }));


        it('should correctly remove selected options', () => {
            store.setState({
                ...store.state,
                selectedFilters: {
                    countries: availableCountries,
                    publishers: availablePublishers,
                    devices: availableDevices,
                },
            });
            expect(store.state.selectedFilters.countries).toEqual([
                {value: 'test country 1', name: 'Test country 1', auctionCount: 1000},
                {value: 'test country 2', name: 'Test country 2', auctionCount: 2000},
            ]);
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 1', name: 'Test publisher 1', auctionCount: 100},
                {value: 'test publisher 2', name: 'Test publisher 2', auctionCount: 200},
            ]);
            expect(store.state.selectedFilters.devices).toEqual([
                {value: 'test device 1', name: 'Test device 1', auctionCount: 10000},
                {value: 'test device 2', name: 'Test device 2', auctionCount: 20000},
            ]);

            store.removeOption({key: 'countries', value: 'test country 1'});
            expect(store.state.selectedFilters.countries).toEqual([
                {value: 'test country 2', name: 'Test country 2', auctionCount: 2000},
            ]);

            store.removeOption({key: 'publishers', value: 'test publisher 1'});
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 2', name: 'Test publisher 2', auctionCount: 200},
            ]);

            store.removeOption({key: 'devices', value: 'test device 1'});
            expect(store.state.selectedFilters.devices).toEqual([
                {value: 'test device 2', name: 'Test device 2', auctionCount: 20000},
            ]);
        });

        it('should skip option with invalid key', () => {
            spyOn(store, 'setState');
            store.removeOption({key: 'invalid', value: 'test value'});
            expect(store.setState).not.toHaveBeenCalled();
        });

        it('should correctly apply filter', () => {
            store.setState({
                ...store.state,
                selectedFilters: {
                    countries: [],
                    publishers: [availablePublishers[0]],
                    devices: availableDevices,
                },
            });
            expect(store.state.selectedFilters.countries).toEqual([]);
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 1', name: 'Test publisher 1', auctionCount: 100},
            ]);
            expect(store.state.selectedFilters.devices).toEqual([
                {value: 'test device 1', name: 'Test device 1', auctionCount: 10000},
                {value: 'test device 2', name: 'Test device 2', auctionCount: 20000},
            ]);

            store.applyFilters([
                {key: 'countries', value: 'test country 1'},
                {key: 'countries', value: 'test country 2'},
                {key: 'publishers', value: 'test publisher 2'},
            ]);

            expect(store.state.selectedFilters.countries).toEqual([
                {value: 'test country 1', name: 'Test country 1', auctionCount: 1000},
                {value: 'test country 2', name: 'Test country 2', auctionCount: 2000},
            ]);
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 2', name: 'Test publisher 2', auctionCount: 200},
            ]);
            expect(store.state.selectedFilters.devices).toEqual([]);
        });

        it('should not apply filter with invalid key', () => {
            store.applyFilters([
                {key: 'invalid', value: 'test value'},
            ]);

            expect(store.state.selectedFilters).toEqual({
                countries: [],
                publishers: [],
                devices: [],
            });
        });
    });
});
