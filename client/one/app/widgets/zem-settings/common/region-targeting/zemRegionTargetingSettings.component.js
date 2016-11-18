// TODO: Fix Performance issues with ui-select - accountManagers (500+)

angular.module('one.widgets').component('zemRegionTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/region-targeting/zemRegionTargetingSettings.component.html',
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.isEqualToDefault = isEqualToDefault;
        $ctrl.isDefault = isDefault;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        function isDefault () {
            if (!$ctrl.entity) return false;
            return !$ctrl.entity.defaultSettings;
        }

        function isEqualToDefault () {
            if (!$ctrl.entity) return false;
            var result = true;

            if ($ctrl.entity.settings.targetRegions.length !== $ctrl.entity.defaultSettings.targetRegions.length) {
                return false;
            }

            $ctrl.entity.settings.targetRegions.forEach(function (region) {
                if ($ctrl.entity.defaultSettings.targetRegions.indexOf(region) === -1) {
                    result = false;
                }
            });

            return result;
        }
    },
});
