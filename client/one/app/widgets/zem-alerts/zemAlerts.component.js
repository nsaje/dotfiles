angular.module('one.widgets').component('zemAlerts', {
    bindings: {
        level: '<',
        entityId: '<'
    },
    templateUrl: '/app/widgets/zem-alerts/zemAlerts.component.html',
    controller: function (zemAlertsService, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            zemAlertsService.refreshAlerts($ctrl.level, $ctrl.entityId);
            zemAlertsService.onAlertsChange(initializeAlerts);
            initializeAlerts();
        };

        function initializeAlerts () {
            $ctrl.alerts = zemAlertsService.getAlerts($ctrl.level, $ctrl.entityId);
        }
    },
});
