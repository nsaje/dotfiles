angular.module('one.widgets').component('zemAdGroupTrackingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemAdGroupTrackingSettings.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function() {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };
    },
});
