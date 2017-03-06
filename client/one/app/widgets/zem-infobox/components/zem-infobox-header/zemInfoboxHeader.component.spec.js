describe('zemInfoboxHeader', function () {
    var $injector;
    var $componentController;
    var $rootScope;
    var $httpBackend;
    var zemEntityService;
    var zemNavigationService;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function (_$injector_) {
        $injector = _$injector_;
        $componentController = $injector.get('$componentController');
        $rootScope = $injector.get('$rootScope');
        $httpBackend = $injector.get('$httpBackend');
        zemEntityService = $injector.get('zemEntityService');
        zemNavigationService = $injector.get('zemNavigationService');

        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});
    }));

    it('should update view when entity updates', function () {
        var $ctrl = $componentController('zemInfoboxHeader');
        var changes = {
            entity: {
                currentValue: undefined,
            },
        };

        $ctrl.$onChanges(changes);
        expect($ctrl.entityName).toEqual(null);

        changes.entity.currentValue = {
            name: 'Test entity',
            type: '',
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.entityName).toEqual('Test entity');
    });

    it('should set correct level text for entity type', function () {
        var $ctrl = $componentController('zemInfoboxHeader');
        var changes = {
            entity: {
                currentValue: undefined,
            },
        };

        $ctrl.$onChanges(changes);
        expect($ctrl.level).toEqual(null);

        changes.entity.currentValue = null;
        $ctrl.$onChanges(changes);
        expect($ctrl.level).toEqual('My accounts');

        changes.entity.currentValue = {
            type: constants.entityType.ACCOUNT,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.level).toEqual('Account');

        changes.entity.currentValue = {
            type: constants.entityType.CAMPAIGN,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.level).toEqual('Campaign');

        changes.entity.currentValue = {
            type: constants.entityType.AD_GROUP,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.level).toEqual('Ad Group');
    });

    it('should only show state switch for ad groups', function () {
        var $ctrl = $componentController('zemInfoboxHeader');
        var changes = {
            entity: {
                currentValue: undefined,
            },
        };

        changes.entity.currentValue = null;
        $ctrl.$onChanges(changes);
        expect($ctrl.isStateSwitchAvailable).toBe(false);

        changes.entity.currentValue = {
            type: constants.entityType.ACCOUNT,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.isStateSwitchAvailable).toBe(false);

        changes.entity.currentValue = {
            type: constants.entityType.CAMPAIGN,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.isStateSwitchAvailable).toBe(false);

        changes.entity.currentValue = {
            type: constants.entityType.AD_GROUP,
            data: {},
        };
        $ctrl.$onChanges(changes);
        expect($ctrl.isStateSwitchAvailable).toBe(true);
    });

    it('should execute activate action when enabling entity', function () {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector);
        var entity = {
            id: 1,
            type: constants.entityType.AD_GROUP,
            data: {
                state: constants.settingsState.INACTIVE
            },
        };
        var bindings = {
            entity: entity,
        };
        var $ctrl = $componentController('zemInfoboxHeader', null, bindings);

        spyOn(zemEntityService, 'executeAction').and.callFake(mockedAsyncFunction);

        $ctrl.toggleEntityState();
        expect(zemEntityService.executeAction).toHaveBeenCalledWith(
            constants.entityAction.ACTIVATE,
            entity.type,
            entity.id
        );
    });

    it('should execute deactivate action when disabling entity', function () {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector);
        var entity = {
            id: 1,
            type: constants.entityType.AD_GROUP,
            data: {
                state: constants.settingsState.ACTIVE
            },
        };
        var bindings = {
            entity: entity,
        };
        var $ctrl = $componentController('zemInfoboxHeader', null, bindings);

        spyOn(zemEntityService, 'executeAction').and.callFake(mockedAsyncFunction);

        $ctrl.toggleEntityState();
        expect(zemEntityService.executeAction).toHaveBeenCalledWith(
            constants.entityAction.DEACTIVATE,
            entity.type,
            entity.id
        );
    });

    it('should call zemNavigationService.reloadAdGroup if action executed successfully', function () {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector, {data: {id: 1}});
        var entity = {
            id: 1,
            type: constants.entityType.AD_GROUP,
            data: {
                state: constants.settingsState.ACTIVE
            },
        };
        var bindings = {
            entity: entity,
        };
        var $ctrl = $componentController('zemInfoboxHeader', null, bindings);

        spyOn(zemEntityService, 'executeAction').and.callFake(mockedAsyncFunction);
        spyOn(zemNavigationService, 'reloadAdGroup').and.stub();

        $ctrl.toggleEntityState();
        $rootScope.$digest();
        expect(zemNavigationService.reloadAdGroup).toHaveBeenCalled();
    });

    it('should show error if action executed unsuccessfully', function () {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector, {data: {message: 'Error message'}}, true
        );
        var entity = {
            id: 1,
            type: constants.entityType.AD_GROUP,
            data: {
                state: constants.settingsState.ACTIVE
            },
        };
        var bindings = {
            entity: entity,
        };
        var $ctrl = $componentController('zemInfoboxHeader', null, bindings);

        spyOn(zemEntityService, 'executeAction').and.callFake(mockedAsyncFunction);

        $ctrl.toggleEntityState();
        $rootScope.$digest();
        expect($ctrl.errorMessage).toEqual('Error message');
    });
});
