angular.module('one.widgets').component('zemGeoTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/geo-targeting/zemGeoTargeting.component.html',
    controller: function (zemGeoTargetingStateService) {
        var $ctrl = this;
        $ctrl.isEqualToDefaultSettings = isEqualToDefaultSettings;
        $ctrl.texts = {
            selectedIncludedTitle: 'Included Locations',
            selectedExcludedTitle: 'Excluded Locations',
            selectTargetingButton: 'Add Location',
            noChoice: 'No available locations',
            defaultTargetingSelected: 'Location targeting is set to Worldwide',
            toggleTargetingEditSection: 'Enable location targeting',
        };

        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function (changes) {
            if (changes.entity && $ctrl.entity) {
                $ctrl.stateService = zemGeoTargetingStateService.createInstance($ctrl.entity);
                $ctrl.state = $ctrl.stateService.getState();
                $ctrl.stateService.init();
            }
        };

        function isEqualToDefaultSettings () {
            if (!$ctrl.state || !$ctrl.entity || !$ctrl.entity.defaultSettings) return true;
            var isTargetRegionsEqual = angular.equals(
                $ctrl.entity.settings.targetRegions,
                $ctrl.entity.defaultSettings.targetRegions
            );
            var isExclusionTargetRegionsEqual = angular.equals(
                $ctrl.entity.settings.exclusionTargetRegions,
                $ctrl.entity.defaultSettings.exclusionTargetRegions
            );
            return isTargetRegionsEqual && isExclusionTargetRegionsEqual;
        }
    }
});
