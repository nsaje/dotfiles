angular.module('one.widgets').component('zemDeviceTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/device-targeting/zemDeviceTargetingSettings.component.html',
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.isEqualToDefault = isEqualToDefault;
        $ctrl.isDefault = isDefault;

        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };

        function isDefault () {
            return !$ctrl.entity.defaultSettings;
        }

        function isEqualToDefault () {
            var isEqualToDefault = true;
            var item, defaultItem;

            options.adTargetDevices.forEach(function (option) {
                item = getDeviceItemByValue($ctrl.entity.settings.targetDevices, option.value);
                defaultItem = getDeviceItemByValue($ctrl.entity.defaultSettings.targetDevices, option.value);

                if (item.checked !== defaultItem.checked) {
                    isEqualToDefault = false;
                }
            });

            return isEqualToDefault;
        }

        function getDeviceItemByValue (devices, value) {
            var result;

            devices.forEach(function (item) {
                if (item.value === value) {
                    result = item;
                }
            });

            return result;
        }
    },
});
