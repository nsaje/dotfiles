angular.module('one.widgets').component('zemDeviceTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<?',
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

        $ctrl.showAdvanceGroup = false;
        $ctrl.isEqualToDefault = isEqualToDefault;
        $ctrl.isDefault = isDefault;

        $ctrl.$onInit = function() {
            if ($ctrl.api) {
                $ctrl.api.register({});
            }
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.entity && $ctrl.entity) {
                if ($ctrl.stateService) $ctrl.stateService.destroy();

                $ctrl.stateService = zemDeviceTargetingStateService.createInstance(
                    $ctrl.entity
                );
                $ctrl.stateService.initialize();
                $ctrl.state = $ctrl.stateService.getState();
                $ctrl.showAdvanceGroup = isAdvanceGroupVisible();
            }
        };

        $ctrl.$onDestroy = function() {
            if ($ctrl.stateService) $ctrl.stateService.destroy();
        };

        function isAdvanceGroupVisible() {
            if ($ctrl.state.operatingSystems.length > 0) return true;

            var selectedPlacements = $ctrl.state.placements.filter(function(p) {
                return p.selected;
            });
            if (selectedPlacements.length !== $ctrl.state.placements.length)
                return true;

            return false;
        }

        function isDefault() {
            if (!$ctrl.state) return false;
            return !$ctrl.state.defaults.devices;
        }

        function isEqualToDefault() {
            if (!$ctrl.state) return false;
            return (
                angular.equals(
                    $ctrl.state.devices,
                    $ctrl.state.defaults.devices
                ) &&
                angular.equals(
                    $ctrl.state.operatingSystems,
                    $ctrl.state.defaults.operatingSystems
                ) &&
                angular.equals(
                    $ctrl.state.placements,
                    $ctrl.state.defaults.placements
                )
            );
        }
    },
});
