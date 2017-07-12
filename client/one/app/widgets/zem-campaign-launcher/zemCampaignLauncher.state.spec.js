describe('zemCampaignLauncherStateService', function () {
    var $injector;
    var $rootScope;
    var zemCampaignLauncherStateService;
    var zemCampaignLauncherEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function (_$injector_) {
        $injector = _$injector_;
        $rootScope = $injector.get('$rootScope');
        zemCampaignLauncherStateService = $injector.get('zemCampaignLauncherStateService');
        zemCampaignLauncherEndpoint = $injector.get('zemCampaignLauncherEndpoint');
    }));

    it('should create new state instance', function () {
        var stateService = zemCampaignLauncherStateService.createInstance();
        expect(stateService.getState).toBeDefined();
    });

    it('should initialize correctly', function () {
        var stateService = zemCampaignLauncherStateService.createInstance();
        stateService.initialize();
        expect(stateService.getState().orderedSteps.length).toEqual(1);
        expect(stateService.getState().currentStep).toEqual(stateService.getState().orderedSteps[0]);
    });

    it('should go to correct step', function () {
        var orderedSteps = [
            {title: 'Test step 1'},
            {title: 'Test step 2'},
            {title: 'Test step 3'},
        ];
        var stateService = zemCampaignLauncherStateService.createInstance();
        var state = stateService.getState();

        state.orderedSteps = orderedSteps;
        stateService.goToStep(orderedSteps[1]);
        expect(stateService.getState().currentStep).toEqual(orderedSteps[1]);
    });

    it('should go to correct step with index', function () {
        var orderedSteps = [
            {title: 'Test step 1'},
            {title: 'Test step 2'},
            {title: 'Test step 3'},
        ];
        var stateService = zemCampaignLauncherStateService.createInstance();
        var state = stateService.getState();

        state.orderedSteps = orderedSteps;
        stateService.goToStepWithIndex(1);
        expect(stateService.getState().currentStep).toEqual(orderedSteps[1]);
    });

    it('should initialize launcher correctly', function () {
        var stateService = zemCampaignLauncherStateService.createInstance();
        stateService.initialize();
        expect(stateService.getState().orderedSteps.length).toEqual(1);
        expect(stateService.getState().currentStep).toEqual(stateService.getState().orderedSteps[0]);
        expect(stateService.getState().campaignObjective).toEqual(null);

        stateService.initLauncherWithObjective(constants.campaignObjective.CONTENT_DISTRIBUTION);
        expect(stateService.getState().orderedSteps.length).toBeGreaterThan(1);
        expect(stateService.getState().currentStep).toEqual(stateService.getState().orderedSteps[1]);
        expect(stateService.getState().campaignObjective).toEqual(constants.campaignObjective.CONTENT_DISTRIBUTION);
        expect(stateService.getState().fields).toEqual({
            campaignName: null,
            iabCategory: null,
            startDate: null,
            endDate: null,
            budgetAmount: null,
            maxCpc: null,
            dailyBudget: null,
            campaignGoal: null,
        });
    });

    it('should correctly determine if step fields are valid', function () {
        var step;
        var validField = {name: 'validField'};
        var fieldWithError = {name: 'fieldWithError'};
        var validRequiredField = {name: 'validRequiredField', required: true};
        var emptyRequiredField = {name: 'emptyRequiredField', required: true};
        var nullRequiredField = {name: 'nullRequiredField', required: true};

        var stateService = zemCampaignLauncherStateService.createInstance();
        var state = stateService.getState();

        step = {fields: [validField]};
        state.fields = {
            validField: 'abc',
        };
        state.fieldsErrors = {};
        expect(stateService.areStepFieldsValid(step)).toBe(true);

        step = {fields: [fieldWithError]};
        state.fields = {
            fieldWithError: 'abc',
        };
        state.fieldsErrors = {
            fieldWithError: 'Error',
        };
        expect(stateService.areStepFieldsValid(step)).toBe(false);

        step = {fields: [validRequiredField]};
        state.fields = {
            validRequiredField: 'abc',
        };
        state.fieldsErrors = {};
        expect(stateService.areStepFieldsValid(step)).toBe(true);

        step = {fields: [emptyRequiredField]};
        state.fields = {
            emptyRequiredField: '',
        };
        state.fieldsErrors = {};
        expect(stateService.areStepFieldsValid(step)).toBe(false);

        step = {fields: [nullRequiredField]};
        state.fields = {
            nullRequiredField: null,
        };
        state.fieldsErrors = {};
        expect(stateService.areStepFieldsValid(step)).toBe(false);
    });

    it('should correctly determine if all steps fields are valid', function () {
        var orderedSteps = [
            {fields: [{name: 'requiredField', required: true}, {name: 'unrequiredField'}]},
            {fields: [{name: 'requiredFieldWithError', required: true}, {name: 'unrequiredFieldWithError'}]},
        ];
        var stateService = zemCampaignLauncherStateService.createInstance();
        var state = stateService.getState();

        state.orderedSteps = orderedSteps;

        state.fields = {
            requiredField: null,
            unrequiredField: null,
            requiredFieldWithError: 'error',
            unrequiredFieldWithError: null,
        };
        state.fieldsErrors = {};
        expect(stateService.areAllStepsValid()).toBe(false);
        state.fields.requiredField = 'valid value';
        expect(stateService.areAllStepsValid()).toBe(true);

        state.fields = {
            requiredField: 'valid value',
            unrequiredField: null,
            requiredFieldWithError: 'error',
            unrequiredFieldWithError: null,
        };
        state.fieldsErrors = {
            requiredFieldWithError: ['error'],
        };
        expect(stateService.areAllStepsValid()).toBe(false);
        state.fieldsErrors.requiredFieldWithError = null;
        expect(stateService.areAllStepsValid()).toBe(true);

        state.fields = {
            requiredField: 'valid value',
            unrequiredField: null,
            requiredFieldWithError: 'error',
            unrequiredFieldWithError: null,
        };
        state.fieldsErrors = {
            unrequiredFieldWithError: ['error'],
        };
        expect(stateService.areAllStepsValid()).toBe(false);
        state.fieldsErrors.unrequiredFieldWithError = null;
        expect(stateService.areAllStepsValid()).toBe(true);
    });


    it('should correctly validate fields', function () {
        var account = {};
        var errors = {
            field1: [],
            field2: [],
            field3: [],
        };
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector, errors, true);
        var stateService = zemCampaignLauncherStateService.createInstance(account);
        var state = stateService.getState();

        state.fields = {
            field1: 'invalid value',
            field2: 'invalid value',
            field3: 'invalid value',
            field4: null,
            field5: 'valid value',
        };

        spyOn(zemCampaignLauncherEndpoint, 'validate').and.callFake(mockedAsyncFunction);
        stateService.validateFields();
        $rootScope.$apply();
        expect(zemCampaignLauncherEndpoint.validate).toHaveBeenCalledWith(account, {
            field1: 'invalid value',
            field2: 'invalid value',
            field3: 'invalid value',
            field5: 'valid value',
        });
        expect(state.fieldsErrors).toEqual(errors);
    });

    it('should correctly launch campaign', function () {
        var account = {};
        var fields = {
            field1: 'value',
            field2: 'value',
            field3: 'value',
        };
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector);
        var stateService = zemCampaignLauncherStateService.createInstance(account);
        var state = stateService.getState();

        state.fields = fields;

        spyOn(zemCampaignLauncherEndpoint, 'launchCampaign').and.callFake(mockedAsyncFunction);
        stateService.launchCampaign();
        $rootScope.$apply();
        expect(zemCampaignLauncherEndpoint.launchCampaign).toHaveBeenCalledWith(account, fields);
        expect(state.requests.launchCampaign.success).toBe(true);
    });

    it('shouldn\'t launch campaign with errors', function () {
        var account = {};
        var fields = {
            field1: 'invalid value',
            field2: 'value',
            field3: 'value',
        };
        var errors = {
            field1: [],
        };
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector, errors, true);
        var stateService = zemCampaignLauncherStateService.createInstance(account);
        var state = stateService.getState();

        state.fields = fields;

        spyOn(zemCampaignLauncherEndpoint, 'launchCampaign').and.callFake(mockedAsyncFunction);
        stateService.launchCampaign();
        $rootScope.$apply();
        expect(zemCampaignLauncherEndpoint.launchCampaign).toHaveBeenCalledWith(account, fields);
        expect(state.requests.launchCampaign.error).toBe(true);
        expect(state.fieldsErrors).toEqual(errors);
    });
});
