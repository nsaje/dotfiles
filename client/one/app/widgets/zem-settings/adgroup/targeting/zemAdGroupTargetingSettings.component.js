angular.module('one.widgets').component('zemAdGroupTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/targeting/zemAdGroupTargetingSettings.component.html',
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.constants = constants;  // interest targeting
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };
    }
});
