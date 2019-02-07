angular.module('one.widgets').component('zemCampaignSettings', {
    bindings: {
        api: '<',
    },
    template: require('./zemCampaignSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.updateGeoTargeting = updateGeoTargeting;
        $ctrl.updateDeviceTargeting = updateDeviceTargeting;

        $ctrl.$onInit = function() {};

        function updateGeoTargeting(entity, $event) {
            if ($event.includedLocations) {
                entity.settings.targetRegions = $event.includedLocations;
            }
            if ($event.excludedLocations) {
                entity.settings.exclusionTargetRegions =
                    $event.excludedLocations;
            }
        }

        function updateDeviceTargeting(entity, $event) {
            entity.settings.targetDevices = $event.targetDevices;
            entity.settings.targetPlacements = $event.targetPlacements;
            entity.settings.targetOs = $event.targetOs;
        }
    },
});
