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

        function updateDaypartingSettings($container, updatedValue) {
            $container.entity.settings.dayparting = updatedValue;
        }
    },
});
