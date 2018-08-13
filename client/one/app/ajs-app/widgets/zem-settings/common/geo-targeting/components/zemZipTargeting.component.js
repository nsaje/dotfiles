angular.module('one.widgets').component('zemZipTargeting', {
    bindings: {
        entity: '<',
        api: '<',
    },
    template: require('./zemZipTargeting.component.html'), // eslint-disable-line max-len
    controller: function($scope, zemZipTargetingStateService) {
        var $ctrl = this;
        var zipTargetingEnabled = false;

        $ctrl.options = options;

        // template functions
        $ctrl.enableZipTargeting = enableZipTargeting;
        $ctrl.isZipTargetingVisible = isZipTargetingVisible;

        $ctrl.$onInit = function() {
            if ($ctrl.api) {
                $ctrl.api.register({});
            }
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.entity && $ctrl.entity) {
                $ctrl.stateService = zemZipTargetingStateService.createInstance(
                    $ctrl.entity
                );
                $ctrl.state = $ctrl.stateService.getState();
                $ctrl.stateService.init();
                initializeWatches();
            }
        };

        function initializeWatches() {
            $scope.$watch('$ctrl.entity.settings.targetRegions', function() {
                $ctrl.stateService.checkConstraints();
            });
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
