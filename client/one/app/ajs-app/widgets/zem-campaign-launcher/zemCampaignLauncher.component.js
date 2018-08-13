require('./zemCampaignLauncher.component.less');

angular.module('one').component('zemCampaignLauncher', {
    bindings: {
        account: '<',
    },
    template: require('./zemCampaignLauncher.component.html'),
    controller: function(zemCampaignLauncherStateService) {
        var $ctrl = this;

        $ctrl.isCurrentStep = isCurrentStep;
        $ctrl.isStepDone = isStepDone;
        $ctrl.isPreviousStepButtonVisible = isPreviousStepButtonVisible;
        $ctrl.isNextStepButtonVisible = isNextStepButtonVisible;
        $ctrl.isReviewButtonVisible = isReviewButtonVisible;
        $ctrl.isLaunchButtonVisible = isLaunchButtonVisible;
        $ctrl.areCurrentStepFieldsValid = areCurrentStepFieldsValid;
        $ctrl.goToPreviousStep = goToPreviousStep;
        $ctrl.goToNextStep = goToNextStep;
        $ctrl.goToReviewStep = goToReviewStep;
        $ctrl.launchCampaign = launchCampaign;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemCampaignLauncherStateService.createInstance(
                $ctrl.account
            );
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();
        };

        function isCurrentStep(step) {
            return $ctrl.state.currentStep === step;
        }

        function isStepDone(step) {
            var stepIndex = $ctrl.state.orderedSteps.indexOf(step);
            var currentStepIndex = $ctrl.state.orderedSteps.indexOf(
                $ctrl.state.currentStep
            );
            return currentStepIndex > stepIndex;
        }

        function isPreviousStepButtonVisible() {
            return (
                $ctrl.state.currentStep &&
                $ctrl.state.currentStep.controls &&
                $ctrl.state.currentStep.controls.previous &&
                !$ctrl.state.requests.launchCampaign.inProgress &&
                $ctrl.state.orderedSteps.indexOf($ctrl.state.currentStep) > 0
            );
        }

        function isNextStepButtonVisible() {
            return (
                $ctrl.state.currentStep &&
                $ctrl.state.currentStep.controls &&
                $ctrl.state.currentStep.controls.next &&
                !$ctrl.state.requests.launchCampaign.inProgress &&
                $ctrl.state.orderedSteps.indexOf($ctrl.state.currentStep) <
                    $ctrl.state.orderedSteps.length - 1
            );
        }

        function isReviewButtonVisible() {
            return (
                $ctrl.state.currentStep &&
                $ctrl.state.currentStep.controls &&
                $ctrl.state.currentStep.controls.review &&
                !$ctrl.state.requests.launchCampaign.inProgress &&
                $ctrl.stateService.areAllStepsValid()
            );
        }

        function isLaunchButtonVisible() {
            return (
                $ctrl.state.currentStep &&
                $ctrl.state.currentStep.controls &&
                $ctrl.state.currentStep.controls.launch &&
                !$ctrl.state.requests.launchCampaign.inProgress
            );
        }

        function areCurrentStepFieldsValid() {
            return $ctrl.stateService.areStepFieldsValid(
                $ctrl.state.currentStep
            );
        }

        function goToPreviousStep() {
            $ctrl.stateService.goToStepWithIndex(
                $ctrl.state.orderedSteps.indexOf($ctrl.state.currentStep) - 1
            );
        }

        function goToNextStep() {
            if (!areCurrentStepFieldsValid()) return;
            $ctrl.stateService.goToStepWithIndex(
                $ctrl.state.orderedSteps.indexOf($ctrl.state.currentStep) + 1
            );
        }

        function goToReviewStep() {
            $ctrl.stateService.goToStep($ctrl.state.steps.review);
        }

        function launchCampaign() {
            $ctrl.stateService.launchCampaign();
        }
    },
});
