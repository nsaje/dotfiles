require('./zemDeviceTargetingSettings.component.less');

angular.module('one.widgets').component('zemDeviceTargetingSettings', {
    bindings: {
        targetDevices: '<',
        targetPlacements: '<',
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
        $ctrl.updatePlacements = updatePlacements;

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
                !$ctrl.targetPlacements ||
                !$ctrl.targetOs
            ) {
                return;
            }
            if (
                changes.targetDevices ||
                changes.targetPlacements ||
                changes.targetOs
            ) {
                $ctrl.stateService.initialize(
                    $ctrl.targetDevices,
                    $ctrl.targetPlacements,
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

            var selectedPlacements = $ctrl.state.placements.filter(function(p) {
                return p.selected;
            });
            if (selectedPlacements.length !== $ctrl.state.placements.length)
                return true;

            return false;
        }

        function updateOperatingSystems($event) {
            $ctrl.state.operatingSystems = $event;
            $ctrl.stateService.update();
        }

        function updatePlacements($event) {
            $ctrl.state.placements = $event;
            $ctrl.stateService.update();
        }
    },
});
