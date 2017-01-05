angular.module('one.widgets').component('zemAccountSettings', {
    bindings: {
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/zemAccountSettings.component.html',
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {};
    },
});
