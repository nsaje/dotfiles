/*globals oneApp,constants,options,moment*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.errors = {};
    $scope.constants = constants;
    $scope.options = options;
    $scope.isStartDatePickerOpen = false;
    $scope.isEndDatePickerOpen = false;
    $scope.datepickerMinDate = moment().add('days', 1).toDate();

    $scope.openDatePicker = function (type) {
        if (type === 'startDate') {
            $scope.isStartDatePickerOpen = true;
        } else if (type === 'endDate') {
            $scope.isEndDatePickerOpen = true;
        }
    };

    $scope.getSettings = function (id) {
        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.settings = data;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.saveSettings = function () {
        api.adGroupSettings.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data;
            },
            function (data) {
                $scope.errors = data;
            }
        );
    };

    $scope.$watch('settings.targetRegions', function (newValue, oldValue) {
        if (newValue && newValue.length) {
            $scope.settings.targetRegionsMode = 'custom';
        }
    }, true);

    $scope.$watch('settings.manualStop', function (newValue, oldValue) {
        if (newValue) {
            $scope.settings.endDate = null;
        }
    });

    $scope.$watch('settings.endDate', function (newValue, oldValue) {
        if (newValue) {
            $scope.settings.manualStop = false;
        } else {
            $scope.settings.manualStop = true;
        }
    });

    $scope.getSettings($state.params.id);
}]);
