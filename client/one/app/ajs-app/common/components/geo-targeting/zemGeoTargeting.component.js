require('./zemGeoTargeting.component.less');

angular.module('one.common').component('zemGeoTargeting', {
    bindings: {
        includedLocations: '<',
        excludedLocations: '<',
        errors: '<',
        onUpdate: '&',
    },
    template: require('./zemGeoTargeting.component.html'),
    controller: function(zemGeoTargetingStateService, zemPermissions) {
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

        $ctrl.texts = {
            selectedIncludedTitle: TEXTS.selectedIncludedTitle,
            selectedExcludedTitle: TEXTS.selectedExcludedTitle,
            selectTargetingButton: TEXTS.selectTargetingButton,
            noChoice: TEXTS.noChoice,
            defaultTargetingSelected: TEXTS.defaultTargetingSelected,
            toggleTargetingEditSection: TEXTS.toggleTargetingEditSection,
        };

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (!$ctrl.stateService) {
                $ctrl.stateService = zemGeoTargetingStateService.createInstance(
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
                setTexts();
            }
        };

        function propagateUpdate(newTargeting) {
            $ctrl.onUpdate({$event: newTargeting});
        }

        $ctrl.isInclusionError = function() {
            return $ctrl.errors && !!($ctrl.errors.targetRegions || []).length;
        };

        $ctrl.isExclusionError = function() {
            return (
                $ctrl.errors &&
                !!($ctrl.errors.exclusionTargetRegions || []).length
            );
        };

        $ctrl.hasTargetingSet = function() {
            if (!$ctrl.state || !$ctrl.includedLocations) {
                return false;
            }

            return (
                $ctrl.includedLocations.postalCodes.length ||
                $ctrl.state.locations.excluded.length ||
                $ctrl.state.locations.included.length
            );
        };

        function setTexts() {
            var zipsPresent =
                hasZips($ctrl.includedLocations) ||
                hasZips($ctrl.excludedLocations);
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
    },
});
