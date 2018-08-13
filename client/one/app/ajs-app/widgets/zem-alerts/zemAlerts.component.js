require('./zemAlerts.component.less');

angular.module('one.widgets').component('zemAlerts', {
    bindings: {
        entity: '<',

        // TODO: remove - legacy support
        level: '<',
        entityId: '<',
    },
    template: require('./zemAlerts.component.html'),
    controller: function(zemAlertsService, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.alertTypes = constants.notificationType;

        $ctrl.$onInit = function() {
            if (!$ctrl.level) {
                $ctrl.level = $ctrl.entity
                    ? constants.entityTypeToLevelMap[$ctrl.entity.type]
                    : constants.level.ALL_ACCOUNTS;
                $ctrl.entityId = $ctrl.entity ? $ctrl.entity.id : null;
            }

            zemAlertsService.refreshAlerts($ctrl.level, $ctrl.entityId);
            zemAlertsService.onAlertsChange(initializeAlerts);
            initializeAlerts();
        };

        function initializeAlerts() {
            $ctrl.alerts = zemAlertsService.getAlerts(
                $ctrl.level,
                $ctrl.entityId
            );
        }
    },
});
