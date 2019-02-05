angular.module('one.widgets').component('zemAdGroupSettings', {
    bindings: {
        api: '<',
    },
    template: require('./zemAdGroupSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.updateDaypartingSettings = updateDaypartingSettings;
        $ctrl.updateBluekaiTargeting = updateBluekaiTargeting;
        $ctrl.updateGeoTargeting = updateGeoTargeting;
        $ctrl.isLocationTargetingDifferentFromDefault = isLocationTargetingDifferentFromDefault;

        function updateDaypartingSettings(entity, $event) {
            entity.settings.dayparting = $event;
        }

        function updateGeoTargeting(entity, $event) {
            if ($event.includedLocations) {
                entity.settings.targetRegions = $event.includedLocations;
            }
            if ($event.excludedLocations) {
                entity.settings.exclusionTargetRegions =
                    $event.excludedLocations;
            }
        }

        function updateBluekaiTargeting(entity, $event) {
            entity.settings.bluekaiTargeting = $event;
        }

        function isLocationTargetingDifferentFromDefault(entity) {
            if (!entity || !entity.defaultSettings) {
                return false;
            }
            var areIncludedRegionsDifferent = !angular.equals(
                entity.settings.targetRegions,
                entity.defaultSettings.targetRegions
            );
            var areExcludedRegionsDifferent = !angular.equals(
                entity.settings.exclusionTargetRegions,
                entity.defaultSettings.exclusionTargetRegions
            );
            return areIncludedRegionsDifferent || areExcludedRegionsDifferent;
        }
    },
});
