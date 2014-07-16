/*globals oneApp,constants,options,moment*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.constants = constants;
    $scope.options = options;
    $scope.isStartDatePickerOpen = false;
    $scope.isEndDatePickerOpen = false;
    $scope.datepickerMinDate = moment().toDate();
    $scope.alerts = [];
    $scope.saveRequestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;

    $scope.closeAlert = function(index) {
        $scope.alerts.splice(index, 1);
    };

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
                $scope.settings = data.settings;
                $scope.actionIsWaiting = data.actionIsWaiting;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.discardSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;
        $scope.errors = {};
        api.adGroupSettings.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.saveRequestInProgress = false;
                $scope.discarded = true;
            },
            function (data) {
                // error
                $scope.saveRequestInProgress = false;
                return;
            }
        );
    };

    $scope.saveSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;
        api.adGroupSettings.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                // $scope.alerts = [{
                //     type: 'info',
                //     message: 'Settings changes are being propagated to external sources. The sync might take a few hours. If you have any questions please contact us at <a href="mailto:help@zemanta.com">help@zemanta.com</a>.'
                // }];
                $scope.updateAccounts($state.params.id, data.name);
                $scope.setBreadcrumb();
                $scope.saveRequestInProgress = false;
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.saveRequestInProgress = false;
                $scope.saved = false;
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
