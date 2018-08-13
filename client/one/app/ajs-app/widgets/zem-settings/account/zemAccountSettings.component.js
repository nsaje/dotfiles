angular.module('one.widgets').component('zemAccountSettings', {
    bindings: {
        api: '<',
    },
    template: require('./zemAccountSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function() {};
    },
});
