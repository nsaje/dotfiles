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
        $ctrl.updateBluekaiTargeting = updateBluekaiTargeting;

        function updateDaypartingSettings($container, updatedValue) {
            $container.entity.settings.dayparting = updatedValue;
        }

        function updateBluekaiTargeting($container, updatedValue) {
            $container.entity.settings.bluekaiTargeting = updatedValue;
        }
    },
});
