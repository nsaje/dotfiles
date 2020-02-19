require('./zemDeviceTargetingSettings.component.less');

angular.module('one.common').component('zemDeviceTargetingSettings', {
    bindings: {
        targetDevices: '<',
        targetEnvironments: '<',
        targetOs: '<',
        errors: '<',
        onUpdate: '&',
    },
    template: require('./zemDeviceTargetingSettings.component.html'),
    controller: function(
        $q,
        config,
        zemPermissions,
        zemDeviceTargetingStateService
    ) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.updateOperatingSystems = updateOperatingSystems;
        $ctrl.updateEnvironments = updateEnvironments;

        $ctrl.showAdvanceGroup = false;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (!$ctrl.stateService) {
                $ctrl.stateService = zemDeviceTargetingStateService.createInstance(
                    propagateUpdate
                );
                $ctrl.state = $ctrl.stateService.getState();
            }
            if (
                !$ctrl.targetDevices ||
                !$ctrl.targetEnvironments ||
                !$ctrl.targetOs
            ) {
                return;
            }
            if (
                changes.targetDevices ||
                changes.targetEnvironments ||
                changes.targetOs
            ) {
                $ctrl.stateService.initialize(
                    $ctrl.targetDevices,
                    $ctrl.targetEnvironments,
                    $ctrl.targetOs
                );
                $ctrl.showAdvanceGroup =
                    $ctrl.showAdvanceGroup || isAdvanceGroupVisible();
            }
        };

        $ctrl.$onDestroy = function() {
            if ($ctrl.stateService) $ctrl.stateService.destroy();
        };

        function propagateUpdate(deviceTargetings) {
            $ctrl.onUpdate({$event: deviceTargetings});
        }

        function isAdvanceGroupVisible() {
            if ($ctrl.state.operatingSystems.length > 0) return true;

            var selectedEnvironments = $ctrl.state.environments.filter(function(
                p
            ) {
                return p.selected;
            });
            if (selectedEnvironments.length !== $ctrl.state.environments.length)
                return true;

            return false;
        }

        function updateOperatingSystems($event) {
            $ctrl.state.operatingSystems = $event;
            $ctrl.stateService.update();
        }

        function updateEnvironments($event) {
            $ctrl.state.environments = $event;
            $ctrl.stateService.update();
        }
    },
});
