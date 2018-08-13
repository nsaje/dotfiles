describe('component: zemCampaignLauncher', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($componentController) {
        var bindings = {};
        $ctrl = $componentController('zemCampaignLauncher', {}, bindings);
        $ctrl.stateService = {
            areStepFieldsValid: function() {},
            areAllStepsValid: function() {},
            goToStep: function() {},
            goToStepWithIndex: function() {},
            launchCampaign: function() {},
        };
        $ctrl.state = {};
        $ctrl.account = {id: 1};
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });

    it('should correctly determine if current step', function() {
        var step1 = {};
        var step2 = {};
        $ctrl.state.currentStep = step1;
        expect($ctrl.isCurrentStep(step1)).toBe(true);
        expect($ctrl.isCurrentStep(step2)).toBe(false);
    });

    it('should correctly determine if step is done', function() {
        var orderedSteps = [
            {title: 'Step 1'},
            {title: 'Step 2'},
            {title: 'Step 3'},
        ];
        $ctrl.state.orderedSteps = orderedSteps;

        $ctrl.state.currentStep = orderedSteps[1];
        expect($ctrl.isStepDone(orderedSteps[0])).toBe(true);
        expect($ctrl.isStepDone(orderedSteps[1])).toBe(false);
        expect($ctrl.isStepDone(orderedSteps[2])).toBe(false);

        $ctrl.state.currentStep = orderedSteps[2];
        expect($ctrl.isStepDone(orderedSteps[0])).toBe(true);
        expect($ctrl.isStepDone(orderedSteps[1])).toBe(true);
        expect($ctrl.isStepDone(orderedSteps[2])).toBe(false);
    });

    it('should correctly determine if previous navigation button is visible', function() {
        var orderedSteps = [
            {controls: {previous: true}},
            {},
            {controls: {previous: true}},
        ];
        $ctrl.state.orderedSteps = orderedSteps;
        $ctrl.state.requests = {launchCampaign: {}};

        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isPreviousStepButtonVisible()).toBeFalsy();

        $ctrl.state.currentStep = orderedSteps[1];
        expect($ctrl.isPreviousStepButtonVisible()).toBeFalsy();

        $ctrl.state.currentStep = orderedSteps[2];
        expect($ctrl.isPreviousStepButtonVisible()).toBeTruthy();

        $ctrl.state.requests = {launchCampaign: {inProgress: true}};
        expect($ctrl.isPreviousStepButtonVisible()).toBeFalsy();
    });

    it('should correctly determine if next navigation button is visible', function() {
        var orderedSteps = [
            {controls: {next: true}},
            {},
            {controls: {next: true}},
        ];
        $ctrl.state.orderedSteps = orderedSteps;

        $ctrl.state.requests = {launchCampaign: {inProgress: true}};
        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isNextStepButtonVisible()).toBeFalsy();

        $ctrl.state.requests = {launchCampaign: {}};
        expect($ctrl.isNextStepButtonVisible()).toBeTruthy();

        $ctrl.state.currentStep = orderedSteps[1];
        expect($ctrl.isNextStepButtonVisible()).toBeFalsy();

        $ctrl.state.currentStep = orderedSteps[2];
        expect($ctrl.isNextStepButtonVisible()).toBeFalsy();
    });

    it('should correctly determine if review navigation button is visible', function() {
        var orderedSteps = [{controls: {review: true}}, {}];
        $ctrl.state.orderedSteps = orderedSteps;
        ($ctrl.stateService.areAllStepsValid = function() {
            return true;
        }),
            ($ctrl.state.requests = {launchCampaign: {inProgress: true}});
        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isReviewButtonVisible()).toBeFalsy();

        $ctrl.state.requests = {launchCampaign: {}};
        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isReviewButtonVisible()).toBeTruthy();

        $ctrl.state.currentStep = orderedSteps[1];
        expect($ctrl.isReviewButtonVisible()).toBeFalsy();
    });

    it('should correctly determine if launch button is visible', function() {
        var orderedSteps = [{controls: {launch: true}}, {}];
        $ctrl.state.orderedSteps = orderedSteps;

        $ctrl.state.requests = {launchCampaign: {inProgress: true}};
        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isLaunchButtonVisible()).toBeFalsy();

        $ctrl.state.requests = {launchCampaign: {}};
        $ctrl.state.currentStep = orderedSteps[0];
        expect($ctrl.isLaunchButtonVisible()).toBeTruthy();

        $ctrl.state.currentStep = orderedSteps[1];
        expect($ctrl.isLaunchButtonVisible()).toBeFalsy();
    });

    it('should correctly determine if current step is valid', function() {
        spyOn($ctrl.stateService, 'areStepFieldsValid').and.stub();
        $ctrl.state.currentStep = {title: 'Current step'};
        $ctrl.areCurrentStepFieldsValid();
        expect($ctrl.stateService.areStepFieldsValid).toHaveBeenCalledWith({
            title: 'Current step',
        });
    });

    it('should correctly navigate to previous step', function() {
        var orderedSteps = [{title: 'Step 1'}, {title: 'Step 2'}];
        spyOn($ctrl.stateService, 'goToStepWithIndex').and.stub();
        $ctrl.state.orderedSteps = orderedSteps;
        $ctrl.state.currentStep = orderedSteps[1];
        $ctrl.goToPreviousStep();
        expect($ctrl.stateService.goToStepWithIndex).toHaveBeenCalledWith(0);
    });

    it('should correctly navigate to next step', function() {
        var orderedSteps = [{title: 'Step 1'}, {title: 'Step 2'}];
        spyOn($ctrl.stateService, 'goToStepWithIndex').and.stub();
        spyOn($ctrl.stateService, 'areStepFieldsValid').and.returnValue(true);
        $ctrl.state.orderedSteps = orderedSteps;
        $ctrl.state.currentStep = orderedSteps[0];
        $ctrl.goToNextStep();
        expect($ctrl.stateService.goToStepWithIndex).toHaveBeenCalledWith(1);
    });

    it('should correctly navigate to review step', function() {
        spyOn($ctrl.stateService, 'goToStep').and.stub();
        $ctrl.state.steps = {review: {title: 'Review'}};
        $ctrl.goToReviewStep();
        expect($ctrl.stateService.goToStep).toHaveBeenCalledWith({
            title: 'Review',
        });
    });

    it('should launch campaign', function() {
        spyOn($ctrl.stateService, 'launchCampaign').and.stub();
        $ctrl.launchCampaign();
        expect($ctrl.stateService.launchCampaign).toHaveBeenCalled();
    });
});
