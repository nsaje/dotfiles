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
        $ctrl.updateDeviceTargeting = updateDeviceTargeting;
        $ctrl.isDeviceTargetingDifferentFromDefault = isDeviceTargetingDifferentFromDefault;
        $ctrl.updateInterestTargeting = updateInterestTargeting;
        $ctrl.updatePublisherGroupsTargeting = updatePublisherGroupsTargeting;
        $ctrl.updateRetargeting = updateRetargeting;

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

        function updateDeviceTargeting(entity, $event) {
            entity.settings.targetDevices = $event.targetDevices;
            entity.settings.targetPlacements = $event.targetPlacements;
            entity.settings.targetOs = $event.targetOs;
        }

        function isDeviceTargetingDifferentFromDefault(entity) {
            if (!entity || !entity.defaultSettings) {
                return false;
            }
            var areTargetDevicesDifferent = !angular.equals(
                entity.settings.targetDevices,
                entity.defaultSettings.targetDevices
            );
            var areTargetOsDifferent = !angular.equals(
                entity.settings.targetOs,
                entity.defaultSettings.targetOs
            );
            var areTargetPlacementsDifferent = !angular.equals(
                entity.settings.targetPlacements,
                entity.defaultSettings.targetPlacements
            );

            return (
                areTargetDevicesDifferent ||
                areTargetOsDifferent ||
                areTargetPlacementsDifferent
            );
        }

        function updateInterestTargeting(entity, $event) {
            if ($event.includedInterests) {
                entity.settings.interestTargeting = $event.includedInterests;
            }
            if ($event.excludedInterests) {
                entity.settings.exclusionInterestTargeting =
                    $event.excludedInterests;
            }
        }

        function updatePublisherGroupsTargeting(entity, $event) {
            if ($event.whitelistedPublisherGroups) {
                entity.settings.whitelistPublisherGroups =
                    $event.whitelistedPublisherGroups;
            }
            if ($event.blacklistedPublisherGroups) {
                entity.settings.blacklistPublisherGroups =
                    $event.blacklistedPublisherGroups;
            }
        }

        function updateRetargeting(entity, $event) {
            if ($event.includedAudiences) {
                entity.settings.audienceTargeting = $event.includedAudiences;
            }
            if ($event.excludedAudiences) {
                entity.settings.exclusionAudienceTargeting =
                    $event.excludedAudiences;
            }
            if ($event.includedAdGroups) {
                entity.settings.retargetingAdGroups = $event.includedAdGroups;
            }
            if ($event.excludedAdGroups) {
                entity.settings.exclusionRetargetingAdGroups =
                    $event.excludedAdGroups;
            }
        }
    },
});
