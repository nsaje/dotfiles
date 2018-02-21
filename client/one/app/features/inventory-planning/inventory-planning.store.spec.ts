import {TestBed, inject} from '@angular/core/testing';
import {HttpClientModule} from '@angular/common/http';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/observable/of';
import {delay} from 'rxjs/operators';

import {InventoryPlanningStore} from './inventory-planning.store';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';

describe('InventoryPlanningStore', () => {
    let store: InventoryPlanningStore;
    let endpoint: InventoryPlanningEndpoint;

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
    const availableSources = [
        {
            value: 'test source 1',
            name: 'Test source 1',
            auctionCount: 100000,
        },
        {
            value: 'test source 2',
            name: 'Test source 2',
            auctionCount: 200000,
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
                Observable.of({auctionCount: 100000, avgCpm: 2, avgCpc: 0.8, winRatio: 0.5}).pipe(delay(0))
            );
            spyOn(endpoint, 'loadCountries').and.returnValue(Observable.of(availableCountries).pipe(delay(0)));
            spyOn(endpoint, 'loadPublishers').and.returnValue(Observable.of(availablePublishers).pipe(delay(0)));
            spyOn(endpoint, 'loadDevices').and.returnValue(Observable.of(availableDevices).pipe(delay(0)));
            spyOn(endpoint, 'loadSources').and.returnValue(Observable.of(availableSources).pipe(delay(0)));

            store = new InventoryPlanningStore(endpoint);
        }));

        it('should correctly refresh data on init', done => {
            store.init();
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
                        sources: {
                            inProgress: false,
                            subscription: null,
                        },
                    },
                    inventory: {auctionCount: 100000, avgCpm: 2, avgCpc: 0.8, winRatio: 0.5},
                    availableFilters: {
                        countries: availableCountries,
                        publishers: availablePublishers,
                        devices: availableDevices,
                        sources: availableSources,
                    },
                    selectedFilters: {
                        countries: [],
                        publishers: [],
                        devices: [],
                        sources: [],
                    },
                });
                done();
            }, 0); // tslint:disable-line align
        });
    });

    describe('without delayed mocked http requests', () => {
        beforeEach(inject([InventoryPlanningEndpoint], (_endpoint: InventoryPlanningEndpoint) => {
            spyOn(_endpoint, 'loadSummary').and.returnValue(
                Observable.of({auctionCount: 100000, avgCpm: 2, avgCpc: 0.8, winRatio: 0.5})
            );
            spyOn(_endpoint, 'loadCountries').and.returnValue(Observable.of(availableCountries));
            spyOn(_endpoint, 'loadPublishers').and.returnValue(Observable.of(availablePublishers));
            spyOn(_endpoint, 'loadDevices').and.returnValue(Observable.of(availableDevices));
            spyOn(_endpoint, 'loadSources').and.returnValue(Observable.of(availableSources));

            endpoint = _endpoint;
            store = new InventoryPlanningStore(_endpoint);
        }));

        it('should make correct requests when initialized with preselected filters', () => {
            store.initWithPreselectedFilters([
                {key: 'countries', value: 'country 1'},
                {key: 'publishers', value: 'publisher 1'},
                {key: 'devices', value: 'device 1'},
                {key: 'sources', value: 'test source 1'},
            ]);
            expect(endpoint.loadCountries).toHaveBeenCalledWith({
                countries: [{name: '', value: 'country 1', auctionCount: -1}],
                publishers: [{name: '', value: 'publisher 1', auctionCount: -1}],
                devices: [{name: '', value: 'device 1', auctionCount: -1}],
                sources: [{name: '', value: 'test source 1', auctionCount: -1}],
            });
        });

        it('should correctly toggle selected options', () => {
            store.setState({
                ...store.state,
                selectedFilters: {
                    countries: availableCountries,
                    publishers: availablePublishers,
                    devices: availableDevices,
                    sources: availableSources,
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
            expect(store.state.selectedFilters.sources).toEqual([
                {value: 'test source 1', name: 'Test source 1', auctionCount: 100000},
                {value: 'test source 2', name: 'Test source 2', auctionCount: 200000},
            ]);

            store.toggleOption({key: 'countries', value: 'test country 1'});
            expect(store.state.selectedFilters.countries).toEqual([
                {value: 'test country 2', name: 'Test country 2', auctionCount: 2000},
            ]);

            store.toggleOption({key: 'publishers', value: 'test publisher 1'});
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 2', name: 'Test publisher 2', auctionCount: 200},
            ]);

            store.toggleOption({key: 'devices', value: 'test device 1'});
            expect(store.state.selectedFilters.devices).toEqual([
                {value: 'test device 2', name: 'Test device 2', auctionCount: 20000},
            ]);

            store.toggleOption({key: 'sources', value: 'test source 1'});
            expect(store.state.selectedFilters.sources).toEqual([
                {value: 'test source 2', name: 'Test source 2', auctionCount: 200000},
            ]);

            store.toggleOption({key: 'countries', value: 'test country 1'});
            expect(store.state.selectedFilters.countries).toEqual([
                {value: 'test country 2', name: 'Test country 2', auctionCount: 2000},
                {value: 'test country 1', name: 'Test country 1', auctionCount: 1000},
            ]);

            store.toggleOption({key: 'publishers', value: 'test publisher 1'});
            expect(store.state.selectedFilters.publishers).toEqual([
                {value: 'test publisher 2', name: 'Test publisher 2', auctionCount: 200},
                {value: 'test publisher 1', name: 'Test publisher 1', auctionCount: 100},
            ]);

            store.toggleOption({key: 'devices', value: 'test device 1'});
            expect(store.state.selectedFilters.devices).toEqual([
                {value: 'test device 2', name: 'Test device 2', auctionCount: 20000},
                {value: 'test device 1', name: 'Test device 1', auctionCount: 10000},
            ]);

            store.toggleOption({key: 'sources', value: 'test source 1'});
            expect(store.state.selectedFilters.sources).toEqual([
                {value: 'test source 2', name: 'Test source 2', auctionCount: 200000},
                {value: 'test source 1', name: 'Test source 1', auctionCount: 100000},
            ]);
        });

        it('should skip option with invalid key on toggle', () => {
            spyOn(store, 'setState');
            store.toggleOption({key: 'invalid', value: 'test value'});
            expect(store.setState).not.toHaveBeenCalled();
        });

        it('should correctly apply filter', () => {
            store.init();
            store.setState({
                ...store.state,
                selectedFilters: {
                    countries: [],
                    publishers: [availablePublishers[0]],
                    devices: availableDevices,
                    sources: availableSources,
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
                sources: [],
            });
        });

        it('should not apply filter with invalid key', () => {
            store.init();
            store.applyFilters([
                {key: 'countries', value: 'test country 1'},
                {key: 'countries', value: 'invalid value'},
            ]);

            expect(store.state.selectedFilters).toEqual({
                countries: [availableCountries[0]],
                publishers: [],
                devices: [],
                sources: [],
            });
        });
    });
});
