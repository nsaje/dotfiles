angular.module('one.widgets').component('zemPerformanceTrackingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/campaign/performance-tracking/zemPerformanceTrackingSettings.component.html', // eslint-disable-line max-len
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        $ctrl.getGaTrackingTypeByValue = function (value) {
            var result;
            for (var i = 0; i < options.gaTrackingType.length; i++) {
                var type = options.gaTrackingType[i];
                if (type.value === value) {
                    result = type;
                    break;
                }
            }
            return result;
        };
    },
});
