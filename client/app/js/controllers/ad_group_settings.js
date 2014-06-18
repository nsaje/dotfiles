/*globals oneApp,constants,options*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.errors = {};
    $scope.constants = constants;
    $scope.options = options;
    $scope.isStartDatePickerOpen = false;
    $scope.isEndDatePickerOpen = false;

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
        $scope.errors = {};
        api.adGroupSettings.save($scope.settings).then(
            function (data) {
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

    $scope.getSettings($state.params.id);
}]);
