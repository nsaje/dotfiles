angular.module('one.widgets').component('zemCampaignTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemCampaignTargetingSettings.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.constants = constants; // interest targeting
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function() {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };
    },
});
