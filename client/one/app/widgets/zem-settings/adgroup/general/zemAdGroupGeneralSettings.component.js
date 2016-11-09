angular.module('one.widgets').component('zemAdGroupGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/general/zemAdGroupGeneralSettings.component.html',
    controller: ['$scope', 'zemPermissions', function ($scope, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.MESSAGES = {
            WARNING_END_DATE: 'Your campaign has been switched to landing mode. ' +
            'Please add the budget and continue to adjust settings by your needs. '
        };

        $ctrl.startDatePicker = {isOpen: false};
        $ctrl.endDatePicker = {isOpen: false};
        $ctrl.endDatePickerOptions = {minDate: new Date()};
        $ctrl.openDatePicker = openDatePicker;

        $ctrl.$onInit = function () {
            initializeWatches();
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        function initializeWatches () {
            // TODO: Refactor - remove the need for watches
            $scope.$watch('$ctrl.entity.settings.manualStop', function (newValue) {
                if (newValue) {
                    $ctrl.entity.settings.endDate = null;
                }
            });

            $scope.$watch('$ctrl.entity.settings.endDate', function (newValue) {
                if (newValue) {
                    $ctrl.entity.settings.manualStop = false;
                } else {
                    $ctrl.entity.settings.manualStop = true;
                }
            });
        }

        function openDatePicker (type) {
            if (type === 'startDate') {
                $ctrl.startDatePicker.isOpen = true;
            } else if (type === 'endDate') {
                $ctrl.endDatePicker.isOpen = true;
            }
        }
    }],
});
