describe('state: zemDeviceTargetingStateService', function() {
    var zemDeviceTargetingStateService, zemPubSubService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        zemDeviceTargetingStateService = $injector.get(
            'zemDeviceTargetingStateService'
        );
        zemPubSubService = $injector.get('zemPubSubService');
    }));

    it('should prepare state object', function() {
        var stateService = zemDeviceTargetingStateService.createInstance(
            angular.noop
        );
        expect(stateService.getState()).toEqual({
            devices: [],
            placements: [],
            operatingSystems: [],
        });
    });

    it('should load the state on initalization', function() {
        var stateService = zemDeviceTargetingStateService.createInstance(
            angular.noop
        );
        var targetDevices = ['MOBILE'];
        var targetPlacements = ['SITE', 'APP'];
        var targetOs = [
            {name: 'IOS', version: {min: 'IOS_4_0', max: null}},
            {name: 'ANDROID', version: {min: 'ANDROID_2_1', max: null}},
        ];

        stateService.initialize(targetDevices, targetPlacements, targetOs);
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
        });
    });

    it('should create pubsub', function() {
        spyOn(zemPubSubService, 'createInstance');
        zemDeviceTargetingStateService.createInstance(angular.noop);
        expect(zemPubSubService.createInstance).toHaveBeenCalled();
    });

    it('should notify updates to the state', function() {
        var callbackSpy = jasmine.createSpy();
        var stateService = zemDeviceTargetingStateService.createInstance(
            callbackSpy
        );
        var targetDevices = ['MOBILE'];
        var targetPlacements = ['SITE', 'APP'];
        var targetOs = [
            {name: 'IOS', version: {min: 'IOS_4_0', max: null}},
            {name: 'ANDROID', version: {min: 'ANDROID_2_1', max: null}},
        ];

        stateService.initialize(targetDevices, targetPlacements, targetOs);

        var spy = jasmine.createSpy();
        stateService.onUpdate(spy);

        stateService.update();
        expect(spy).toHaveBeenCalled();
        expect(callbackSpy).toHaveBeenCalled();
    });

    it('should update settings on state update', function() {
        var callbackSpy = jasmine.createSpy();
        var stateService = zemDeviceTargetingStateService.createInstance(
            callbackSpy
        );
        var targetDevices = ['MOBILE'];
        var targetPlacements = ['SITE', 'APP'];
        var targetOs = [{name: 'IOS', version: {min: 'IOS_4_0', max: null}}];

        stateService.initialize(targetDevices, targetPlacements, targetOs);

        var state = stateService.getState();

        state.devices[0].checked = true;
        state.placements[0].selected = false;
        stateService.update();

        expect(callbackSpy).toHaveBeenCalledWith({
            targetDevices: ['DESKTOP', 'MOBILE'],
            targetOs: [{name: 'IOS', version: {min: 'IOS_4_0'}}],
            targetPlacements: ['APP'],
        });
    });

    it('should configure OS max version to be always greater than min', function() {
        var stateService = zemDeviceTargetingStateService.createInstance(
            angular.noop
        );
        var targetOs = [
            {name: 'IOS', version: {min: 'IOS_4_0', max: 'IOS_7_0'}},
        ];

        stateService.initialize(null, null, targetOs);

        var os = stateService.getState().operatingSystems[0];
        os.version.max = os.versions[1];
        stateService.update();

        expect(stateService.getState().operatingSystems[0].version).toEqual({
            min: {value: 'IOS_4_0', name: '4.0'},
            max: {value: 'IOS_4_0', name: '4.0'},
        });
    });
});
