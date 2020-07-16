import {TestBed, inject} from '@angular/core/testing';
import {HttpClientModule} from '@angular/common/http';
import {of} from 'rxjs';
import {delay} from 'rxjs/operators';

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
    const availableChannels = [
        {
            value: 'test traffic 1',
            name: 'Test traffic 1',
            auctionCount: 100000,
        },
        {
            value: 'test traffic 2',
            name: 'Test traffic 2',
            auctionCount: 200000,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientModule],
            providers: [InventoryPlanningEndpoint],
        });
    });

    describe('with delayed mocked http requests', () => {
        let endpointSpy: any;

        beforeEach(inject(
            [InventoryPlanningEndpoint],
            (endpoint: InventoryPlanningEndpoint) => {
                endpointSpy = jasmine.createSpyObj(
                    'InventoryPlanningEndpoint',
                    [
                        'loadSummary',
                        'loadCountries',
                        'loadPublishers',
                        'loadDevices',
                        'loadSources',
                        'loadChannels',
                    ]
                );

                endpointSpy.loadSummary.and.returnValue(
                    of({
                        auctionCount: 100000,
                        avgCpm: 2,
                        avgCpc: 0.8,
                        winRatio: 0.5,
                    }).pipe(delay(0))
                );

                endpointSpy.loadCountries.and.returnValue(
                    of(availableCountries).pipe(delay(0))
                );

                endpointSpy.loadPublishers.and.returnValue(
                    of(availablePublishers).pipe(delay(0))
                );

                endpointSpy.loadDevices.and.returnValue(
                    of(availableDevices).pipe(delay(0))
                );

                endpointSpy.loadSources.and.returnValue(
                    of(availableSources).pipe(delay(0))
                );

                endpointSpy.loadChannels.and.returnValue(
                    of(availableChannels).pipe(delay(0))
                );

                store = new InventoryPlanningStore(endpointSpy);
            }
        ));

        it('should correctly refresh data on init', done => {
            store.init();
            setTimeout(() => {
                expect(store.state).toEqual(
                    jasmine.objectContaining({
                        inventory: {
                            auctionCount: 100000,
                            avgCpm: 2,
                            avgCpc: 0.8,
                            winRatio: 0.5,
                        },
                        availableFilters: {
                            countries: availableCountries,
                            publishers: availablePublishers,
                            devices: availableDevices,
                            sources: availableSources,
                            channels: availableChannels,
                        },
                        selectedFilters: {
                            countries: [],
                            publishers: [],
                            devices: [],
                            sources: [],
                            channels: [],
                        },
                    })
                );
                done();
            }, 0); // tslint:disable-line align
        });
    });

    describe('without delayed mocked http requests', () => {
        let endpointSpy: any;

        beforeEach(inject(
            [InventoryPlanningEndpoint],
            (_endpoint: InventoryPlanningEndpoint) => {
                endpointSpy = jasmine.createSpyObj(
                    'InventoryPlanningEndpoint',
                    [
                        'loadSummary',
                        'loadCountries',
                        'loadPublishers',
                        'loadDevices',
                        'loadSources',
                        'loadChannels',
                    ]
                );

                endpointSpy.loadSummary.and.returnValue(
                    of({
                        auctionCount: 100000,
                        avgCpm: 2,
                        avgCpc: 0.8,
                        winRatio: 0.5,
                    })
                );

                endpointSpy.loadCountries.and.returnValue(
                    of(availableCountries)
                );

                endpointSpy.loadPublishers.and.returnValue(
                    of(availablePublishers)
                );

                endpointSpy.loadDevices.and.returnValue(of(availableDevices));

                endpointSpy.loadSources.and.returnValue(of(availableSources));

                endpointSpy.loadChannels.and.returnValue(of(availableChannels));

                store = new InventoryPlanningStore(endpointSpy);
            }
        ));

        it('should make correct requests when initialized with preselected filters', () => {
            store.initWithPreselectedFilters([
                {key: 'countries', value: 'country 1'},
                {key: 'publishers', value: 'publisher 1'},
                {key: 'devices', value: 'device 1'},
                {key: 'sources', value: 'test source 1'},
                {key: 'channels', value: 'test traffic 1'},
            ]);
            expect(endpointSpy.loadCountries).toHaveBeenCalledWith(
                {
                    countries: [
                        {name: '', value: 'country 1', auctionCount: -1},
                    ],
                    publishers: [
                        {name: '', value: 'publisher 1', auctionCount: -1},
                    ],
                    devices: [{name: '', value: 'device 1', auctionCount: -1}],
                    sources: [
                        {name: '', value: 'test source 1', auctionCount: -1},
                    ],
                    channels: [
                        {name: '', value: 'test traffic 1', auctionCount: -1},
                    ],
                },
                jasmine.any(Function)
            );
        });

        it('should correctly toggle selected options', () => {
            store.init();
            store.setState({
                ...store.state,
                selectedFilters: {
                    countries: availableCountries,
                    publishers: availablePublishers,
                    devices: availableDevices,
                    sources: availableSources,
                    channels: availableChannels,
                },
            });
            expect(store.state.selectedFilters.countries).toEqual([
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
            ]);
            expect(store.state.selectedFilters.publishers).toEqual([
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
            ]);
            expect(store.state.selectedFilters.devices).toEqual([
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
            ]);
            expect(store.state.selectedFilters.sources).toEqual([
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
            ]);
            expect(store.state.selectedFilters.channels).toEqual([
                {
                    value: 'test traffic 1',
                    name: 'Test traffic 1',
                    auctionCount: 100000,
                },
                {
                    value: 'test traffic 2',
                    name: 'Test traffic 2',
                    auctionCount: 200000,
                },
            ]);

            store.toggleOption({key: 'countries', value: 'test country 1'});
            expect(store.state.selectedFilters.countries).toEqual([
                {
                    value: 'test country 2',
                    name: 'Test country 2',
                    auctionCount: 2000,
                },
            ]);

            store.toggleOption({key: 'publishers', value: 'test publisher 1'});
            expect(store.state.selectedFilters.publishers).toEqual([
                {
                    value: 'test publisher 2',
                    name: 'Test publisher 2',
                    auctionCount: 200,
                },
            ]);

            store.toggleOption({key: 'devices', value: 'test device 1'});
            expect(store.state.selectedFilters.devices).toEqual([
                {
                    value: 'test device 2',
                    name: 'Test device 2',
                    auctionCount: 20000,
                },
            ]);

            store.toggleOption({key: 'sources', value: 'test source 1'});
            expect(store.state.selectedFilters.sources).toEqual([
                {
                    value: 'test source 2',
                    name: 'Test source 2',
                    auctionCount: 200000,
                },
            ]);

            store.toggleOption({key: 'channels', value: 'test traffic 1'});
            expect(store.state.selectedFilters.channels).toEqual([
                {
                    value: 'test traffic 2',
                    name: 'Test traffic 2',
                    auctionCount: 200000,
                },
            ]);

            store.toggleOption({key: 'countries', value: 'test country 1'});
            expect(store.state.selectedFilters.countries).toEqual([
                {
                    value: 'test country 2',
                    name: 'Test country 2',
                    auctionCount: 2000,
                },
                {
                    value: 'test country 1',
                    name: 'Test country 1',
                    auctionCount: 1000,
                },
            ]);

            store.toggleOption({key: 'publishers', value: 'test publisher 1'});
            expect(store.state.selectedFilters.publishers).toEqual([
                {
                    value: 'test publisher 2',
                    name: 'Test publisher 2',
                    auctionCount: 200,
                },
                {
                    value: 'test publisher 1',
                    name: 'Test publisher 1',
                    auctionCount: 100,
                },
            ]);

            store.toggleOption({key: 'devices', value: 'test device 1'});
            expect(store.state.selectedFilters.devices).toEqual([
                {
                    value: 'test device 2',
                    name: 'Test device 2',
                    auctionCount: 20000,
                },
                {
                    value: 'test device 1',
                    name: 'Test device 1',
                    auctionCount: 10000,
                },
            ]);

            store.toggleOption({key: 'sources', value: 'test source 1'});
            expect(store.state.selectedFilters.sources).toEqual([
                {
                    value: 'test source 2',
                    name: 'Test source 2',
                    auctionCount: 200000,
                },
                {
                    value: 'test source 1',
                    name: 'Test source 1',
                    auctionCount: 100000,
                },
            ]);

            store.toggleOption({key: 'channels', value: 'test traffic 1'});
            expect(store.state.selectedFilters.channels).toEqual([
                {
                    value: 'test traffic 2',
                    name: 'Test traffic 2',
                    auctionCount: 200000,
                },
                {
                    value: 'test traffic 1',
                    name: 'Test traffic 1',
                    auctionCount: 100000,
                },
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
                    sources: [availableSources[0]],
                    channels: [availableChannels[0]],
                },
            });
            expect(store.state.selectedFilters.countries).toEqual([]);
            expect(store.state.selectedFilters.publishers).toEqual([
                {
                    value: 'test publisher 1',
                    name: 'Test publisher 1',
                    auctionCount: 100,
                },
            ]);
            expect(store.state.selectedFilters.devices).toEqual([
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
            ]);
            expect(store.state.selectedFilters.sources).toEqual([
                {
                    value: 'test source 1',
                    name: 'Test source 1',
                    auctionCount: 100000,
                },
            ]);
            expect(store.state.selectedFilters.channels).toEqual([
                {
                    value: 'test traffic 1',
                    name: 'Test traffic 1',
                    auctionCount: 100000,
                },
            ]);

            store.applyFilters([
                {key: 'countries', value: 'test country 1'},
                {key: 'countries', value: 'test country 2'},
                {key: 'publishers', value: 'test publisher 2'},
            ]);

            expect(store.state.selectedFilters.countries).toEqual([
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
            ]);
            expect(store.state.selectedFilters.publishers).toEqual([
                {
                    value: 'test publisher 2',
                    name: 'Test publisher 2',
                    auctionCount: 200,
                },
            ]);
            expect(store.state.selectedFilters.devices).toEqual([]);
        });

        it('should not apply filter with invalid key', () => {
            store.applyFilters([{key: 'invalid', value: 'test value'}]);

            expect(store.state.selectedFilters).toEqual({
                countries: [],
                publishers: [],
                devices: [],
                sources: [],
                channels: [],
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
                channels: [],
            });
        });
    });
});
