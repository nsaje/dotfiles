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

        $ctrl.$onInit = function() {};

        function updateGeoTargeting(entity, updatedGeoTargeting) {
            if (updatedGeoTargeting.includedLocations) {
                entity.settings.targetRegions =
                    updatedGeoTargeting.includedLocations;
            }
            if (updatedGeoTargeting.excludedLocations) {
                entity.settings.exclusionTargetRegions =
                    updatedGeoTargeting.excludedLocations;
            }
        }
    },
});
