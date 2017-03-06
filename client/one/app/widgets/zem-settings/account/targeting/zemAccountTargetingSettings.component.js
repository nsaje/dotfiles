angular.module('one.widgets').component('zemAccountTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/targeting/zemAccountTargetingSettings.component.html',
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