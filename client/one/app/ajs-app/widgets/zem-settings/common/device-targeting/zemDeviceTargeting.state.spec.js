describe('state: zemDeviceTargetingStateService', function() {
    var zemDeviceTargetingStateService,
        zemPubSubService,
        zemDeviceTargetingConstants;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        zemDeviceTargetingStateService = $injector.get(
            'zemDeviceTargetingStateService'
        );
        zemDeviceTargetingConstants = $injector.get(
            'zemDeviceTargetingConstants'
        );
        zemPubSubService = $injector.get('zemPubSubService');
    }));

    it('should prepare state object', function() {
        var stateService = zemDeviceTargetingStateService.createInstance({});
        expect(stateService.getState()).toEqual({
            devices: null,
            placements: null,
            operatingSystems: null,
            defaults: {
                devices: null,
                placements: null,
                operatingSystems: null,
            },
        });
    });

    it('should load the state on initalization', function() {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['MOBILE'],
                targetOs: [
                    {name: 'IOS', version: {min: 'IOS_4_0', max: null}},
                    {name: 'ANDROID', version: {min: 'ANDROID_2_1', max: null}},
                ],
                targetPlacements: ['SITE', 'APP'],
            },
        });
        stateService.initialize();
        expect(stateService.getState()).toEqual({
            devices: [
                {name: 'Desktop', value: 'DESKTOP', checked: false},
                {name: 'Tablet', value: 'TABLET', checked: false},
                {name: 'Mobile', value: 'MOBILE', checked: true},
            ],
            placements: [
                {
                    value: 'SITE',
                    name: 'Website',
                    devices: ['DESKTOP', 'MOBILE', 'TABLET'],
                    selected: true,
                },
                {
                    value: 'APP',
                    name: 'In-app',
                    devices: ['MOBILE', 'TABLET'],
                    selected: true,
                },
            ],
            operatingSystems: [
                {
                    devices: ['MOBILE', 'TABLET'],
                    value: 'IOS',
                    name: 'Apple iOS',
                    versions: jasmine.any(Object),
                    version: {
                        min: {value: 'IOS_4_0', name: '4.0'},
                        max: {value: null, name: ' - '},
                    },
                },
                {
                    devices: ['MOBILE', 'TABLET'],
                    value: 'ANDROID',
                    name: 'Google Android',
                    versions: jasmine.any(Object),
                    version: {
                        min: {value: 'ANDROID_2_1', name: '2.1 Eclair'},
                        max: {value: null, name: ' - '},
                    },
                },
            ],
            defaults: {
                devices: null,
                operatingSystems: null,
                placements: null,
            },
        });
    });

    it('should create pubsub', function() {
        spyOn(zemPubSubService, 'createInstance');
        zemDeviceTargetingStateService.createInstance({});
        expect(zemPubSubService.createInstance).toHaveBeenCalled();
    });

    it('should notify updates to the state', function() {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['MOBILE'],
            },
        });

        stateService.initialize();

        var spy = jasmine.createSpy();
        stateService.onUpdate(spy);

        stateService.update();
        expect(spy).toHaveBeenCalled();
    });

    it('should notify on operatingSystem updates', function() {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['DESKTOP'],
                targetOs: [],
            },
        });

        stateService.initialize();
        var spy = jasmine.createSpy();
        stateService.onUpdate(spy);

        stateService.addOperatingSystem(
            zemDeviceTargetingConstants.OPERATING_SYSTEMS[0]
        );
        expect(spy).toHaveBeenCalled();
        spy.calls.reset();

        stateService.removeOperatingSystem(
            stateService.getState().operatingSystems[0]
        );
        expect(spy).toHaveBeenCalled();
    });

    it('should update settings on state update', function() {
        var entity = {
            settings: {
                targetDevices: ['MOBILE'],
                targetOs: [{name: 'IOS', version: {min: 'IOS_4_0', max: null}}],
                targetPlacements: ['SITE', 'APP'],
            },
        };

        var stateService = zemDeviceTargetingStateService.createInstance(
            entity
        );
        stateService.initialize();

        var state = stateService.getState();

        state.devices[0].checked = true;
        state.placements[0].selected = false;
        stateService.update();

        expect(entity.settings).toEqual({
            targetDevices: ['DESKTOP', 'MOBILE'],
            targetOs: [{name: 'IOS', version: {min: 'IOS_4_0'}}],
            targetPlacements: ['APP'],
        });
    });

    it('should configure OS max version to be always greater than min', function() {
        var entity = {
            settings: {
                targetOs: [
                    {name: 'IOS', version: {min: 'IOS_4_0', max: 'IOS_7_0'}},
                ],
            },
        };

        var stateService = zemDeviceTargetingStateService.createInstance(
            entity
        );
        stateService.initialize();

        var os = stateService.getState().operatingSystems[0];
        os.version.max = os.versions[1];
        stateService.update();

        expect(stateService.getState().operatingSystems[0].version).toEqual({
            min: {value: 'IOS_4_0', name: '4.0'},
            max: {value: 'IOS_4_0', name: '4.0'},
        });
    });
});
