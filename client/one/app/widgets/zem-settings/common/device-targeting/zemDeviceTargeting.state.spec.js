describe('state: zemDeviceTargetingStateService', function () {
    var zemDeviceTargetingStateService, zemPubSubService, zemDeviceTargetingConstants;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function ($injector) {
        zemDeviceTargetingStateService = $injector.get('zemDeviceTargetingStateService');
        zemDeviceTargetingConstants = $injector.get('zemDeviceTargetingConstants');
        zemPubSubService = $injector.get('zemPubSubService');
    }));

    it('should prepare state object', function () {
        var stateService = zemDeviceTargetingStateService.createInstance({});
        expect(stateService.getState()).toEqual({
            devices: null,
            placements: null,
            operatingSystems: null,
            defaults: {
                devices: null,
                placements: null,
                operatingSystems: null,
            }
        });
    });

    it('should load the state on initalization', function () {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['mobile'],
                targetOs: [
                    {name: 'ios', version: {min: 'ios_4_0', max: null}},
                    {name: 'android', version: {min: 'android_2_1', max: null}}
                ],
                targetPlacements: ['site', 'app']
            }
        });
        stateService.initialize();
        expect(stateService.getState()).toEqual(
            {
                devices: [
                    {name: 'Desktop', value: 'desktop', checked: false},
                    {name: 'Tablet', value: 'tablet', checked: false},
                    {name: 'Mobile', value: 'mobile', checked: true}
                ],
                placements: [
                    {value: 'site', name: 'Website', devices: ['desktop', 'mobile', 'tablet'], selected: true},
                    {value: 'app', name: 'In-app', devices: ['mobile', 'tablet'], selected: true}
                ],
                operatingSystems: [
                    {
                        devices: ['mobile', 'tablet'],
                        value: 'ios',
                        name: 'Apple iOS',
                        versions: jasmine.any(Object),
                        version: {min: {value: 'ios_4_0', name: '4.0'}, max: {value: null, name: ' - '}}
                    },
                    {
                        devices: ['mobile', 'tablet'],
                        value: 'android',
                        name: 'Google Android',
                        versions: jasmine.any(Object),
                        version: {min: {value: 'android_2_1', name: '2.1 Eclair'}, max: {value: null, name: ' - '}}
                    }
                ],
                defaults: {
                    devices: null,
                    operatingSystems: null,
                    placements: null,
                }
            });
    });

    it('should create pubsub', function () {
        spyOn(zemPubSubService, 'createInstance');
        zemDeviceTargetingStateService.createInstance({});
        expect(zemPubSubService.createInstance).toHaveBeenCalled();
    });

    it('should notify updates to the state', function () {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['mobile'],
            }
        });

        stateService.initialize();

        var spy = jasmine.createSpy();
        stateService.onUpdate(spy);

        stateService.update();
        expect(spy).toHaveBeenCalled();
    });

    it('should notify on operatingSystem updates', function () {
        var stateService = zemDeviceTargetingStateService.createInstance({
            settings: {
                targetDevices: ['desktop'],
                targetOs: [],
            }
        });

        stateService.initialize();
        var spy = jasmine.createSpy();
        stateService.onUpdate(spy);

        stateService.addOperatingSystem(zemDeviceTargetingConstants.OPERATING_SYSTEMS[0]);
        expect(spy).toHaveBeenCalled();
        spy.calls.reset();

        stateService.removeOperatingSystem(stateService.getState().operatingSystems[0]);
        expect(spy).toHaveBeenCalled();
    });


    it('should update settings on state update', function () {
        var entity = {
            settings: {
                targetDevices: ['mobile'],
                targetOs: [{name: 'ios', version: {min: 'ios_4_0', max: null}}],
                targetPlacements: ['site', 'app']
            }
        };

        var stateService = zemDeviceTargetingStateService.createInstance(entity);
        stateService.initialize();

        var state = stateService.getState();

        state.devices[0].checked = true;
        state.placements[0].selected = false;
        stateService.update();

        expect(entity.settings).toEqual({
            targetDevices: ['desktop', 'mobile'],
            targetOs: [{name: 'ios', version: {min: 'ios_4_0', max: null}}],
            targetPlacements: ['app']
        });
    });

    it('should configure OS max version to be always greater than min', function () {
        var entity = {
            settings: {
                targetOs: [{name: 'ios', version: {min: 'ios_4_0', max: 'ios_7_0'}}],
            }
        };

        var stateService = zemDeviceTargetingStateService.createInstance(entity);
        stateService.initialize();

        var os = stateService.getState().operatingSystems[0];
        os.version.max = os.versions[1];
        stateService.update();

        expect(stateService.getState().operatingSystems[0].version).toEqual ({
            min: {value: 'ios_4_0', name: '4.0'},
            max: {value: 'ios_4_0', name: '4.0'}
        });
    });
});
