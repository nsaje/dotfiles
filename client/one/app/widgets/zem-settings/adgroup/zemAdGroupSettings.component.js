angular.module('one.widgets').component('zemAdGroupSettings', {
    bindings: {
        entityId: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/zemAdGroupSettings.component.html',
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () { };
    },
});
