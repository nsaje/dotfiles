angular.module('one.widgets').component('zemAlerts', {
    bindings: {
        level: '<',
        entityId: '<'
    },
    templateUrl: '/app/widgets/zem-alerts/zemAlerts.component.html',
    controller: ['zemAlertsService', 'zemUserService', function (zemAlertsService, zemUserService) {
        var $ctrl = this;
        $ctrl.userHasPermissions = zemUserService.userHasPermissions;
        $ctrl.isPermissionInternal = zemUserService.isPermissionInternal;

        $ctrl.$onInit = function () {
            zemAlertsService.refreshAlerts($ctrl.level, $ctrl.entityId);
            zemAlertsService.onAlertsChange(initializeAlerts);
            initializeAlerts();
        };

        function initializeAlerts () {
            $ctrl.alerts = zemAlertsService.getAlerts($ctrl.level, $ctrl.entityId);
        }
    }],
});
