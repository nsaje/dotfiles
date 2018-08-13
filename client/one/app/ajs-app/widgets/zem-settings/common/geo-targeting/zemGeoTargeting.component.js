angular.module('one.widgets').component('zemGeoTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<?',
    },
    template: require('./zemGeoTargeting.component.html'),
    controller: function($scope, zemGeoTargetingStateService, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        var TEXTS = {
            selectedIncludedTitle: 'Included Locations',
            selectedExcludedTitle: 'Excluded Locations',
            selectTargetingButton: 'Add Location',
            noChoice: 'No available locations',
            defaultTargetingSelected: 'Location targeting is set to Worldwide.',
            postalCodeTargeting:
                'Location targeting is set to Postal Code targeting.',
            toggleTargetingEditSection: 'Enable location targeting',
            addAdditionalLocationTargeting: 'Add additional location targeting',
        };

        $ctrl.isEqualToDefaultSettings = isEqualToDefaultSettings;

        $ctrl.texts = {
            selectedIncludedTitle: TEXTS.selectedIncludedTitle,
            selectedExcludedTitle: TEXTS.selectedExcludedTitle,
            selectTargetingButton: TEXTS.selectTargetingButton,
            noChoice: TEXTS.noChoice,
            defaultTargetingSelected: TEXTS.defaultTargetingSelected,
            toggleTargetingEditSection: TEXTS.toggleTargetingEditSection,
        };

        $ctrl.$onInit = function() {
            if ($ctrl.api) {
                $ctrl.api.register({});
            }
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.entity && $ctrl.entity) {
                $ctrl.stateService = zemGeoTargetingStateService.createInstance(
                    $ctrl.entity
                );
                $ctrl.state = $ctrl.stateService.getState();

                $ctrl.stateService.init();
                initializeWatches();
                setTexts();
            }
        };

        $ctrl.isInclusionError = function() {
            return $ctrl.errors && !!($ctrl.errors.targetRegions || []).length;
        };

        $ctrl.isExclusionError = function() {
            return (
                $ctrl.errors &&
                !!($ctrl.errors.exclusionTargetRegions || []).length
            );
        };

        function initializeWatches() {
            var watchExpressions = [
                '$ctrl.entity.settings.targetRegions',
                '$ctrl.entity.settings.exclusionTargetRegions',
            ];
            $scope.$watchGroup(watchExpressions, setTexts);
        }

        function setTexts() {
            var zipsPresent =
                hasZips($ctrl.entity.settings.targetRegions) ||
                hasZips($ctrl.entity.settings.exclusionTargetRegions);
            if (zipsPresent) {
                $ctrl.texts.defaultTargetingSelected =
                    TEXTS.postalCodeTargeting;
                $ctrl.texts.toggleTargetingEditSection =
                    TEXTS.addAdditionalLocationTargeting;
            } else {
                $ctrl.texts.defaultTargetingSelected =
                    TEXTS.defaultTargetingSelected;
                $ctrl.texts.toggleTargetingEditSection =
                    TEXTS.toggleTargetingEditSection;
            }
        }

        function hasZips(regions) {
            return regions[constants.geolocationType.ZIP];
        }

        function isEqualToDefaultSettings() {
            if (!$ctrl.state || !$ctrl.entity || !$ctrl.entity.defaultSettings)
                return true;
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
    },
});
