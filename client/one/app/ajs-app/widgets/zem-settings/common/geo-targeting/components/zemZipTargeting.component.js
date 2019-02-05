angular.module('one.widgets').component('zemZipTargeting', {
    bindings: {
        includedLocations: '<',
        excludedLocations: '<',
        onUpdate: '&',
    },
    template: require('./zemZipTargeting.component.html'), // eslint-disable-line max-len
    controller: function(zemZipTargetingStateService) {
        var $ctrl = this;
        var zipTargetingEnabled = false;

        $ctrl.options = options;

        $ctrl.enableZipTargeting = enableZipTargeting;
        $ctrl.isZipTargetingVisible = isZipTargetingVisible;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (!$ctrl.stateService) {
                $ctrl.stateService = zemZipTargetingStateService.createInstance(
                    propagateUpdate
                );
                $ctrl.state = $ctrl.stateService.getState();
            }
            if (!$ctrl.includedLocations || !$ctrl.excludedLocations) {
                return;
            }
            if (changes.includedLocations || changes.excludedLocations) {
                $ctrl.stateService.updateTargeting(
                    $ctrl.includedLocations,
                    $ctrl.excludedLocations
                );
            }
        };

        function propagateUpdate(newTargeting) {
            $ctrl.onUpdate({$event: newTargeting});
        }

        function enableZipTargeting() {
            zipTargetingEnabled = true;
        }

        function isZipTargetingVisible() {
            if (!$ctrl.state) {
                return false;
            }
            return (
                zipTargetingEnabled ||
                $ctrl.state.textareaContent.length ||
                $ctrl.state.blockers.apiOnlySettings
            );
        }
    },
});
