/*globals oneApp,constants,options*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', 'regions', function ($scope, $state, $q, $timeout, api, regions) {
    var freshSettings = $q.defer(),
        goToContentAds = false;
    $scope.settings = {};
    $scope.loadRequestInProgress = true;
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.regions = regions;
    $scope.options = options;
    $scope.alerts = [];
    $scope.saveRequestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.minEndDate = new Date();

    // isOpen has to be an object property instead
    // of being directly on $scope because
    // datepicker-popup directive creates a new child
    // scope which breaks two-way binding in that case
    // https://github.com/angular/angular.js/wiki/Understanding-Scopes
    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};

    $scope.adGroupHasFreshSettings = function () {
        return freshSettings.promise;
    };

    $scope.closeAlert = function (index) {
        $scope.alerts.splice(index, 1);
    };

    $scope.openDatePicker = function (type) {
        if (type === 'startDate') {
            $scope.startDatePicker.isOpen = true;
        } else if (type === 'endDate') {
            $scope.endDatePicker.isOpen = true;
        }
    };

    var getAdGroupStatus = function (settings) {
        var now = new Date(),
            running0 = settings.state === constants.adGroupSettingsState.ACTIVE,
            running1 = settings.endDate && (now <= moment(settings.endDate).toDate() && moment(settings.startDate).toDate() <= now),
            running2 = !settings.endDate && (moment(settings.startDate).toDate() <= now);
        return running0 && (running1 || running2) ? 'running' : 'stopped';
    };

    $scope.getSettings = function (id) {
        $scope.loadRequestInProgress = true;

        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.defaultSettings = data.defaultSettings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.setAdGroupPaused($scope.settings.state === constants.adGroupSettingsState.INACTIVE);
                freshSettings.resolve(data.settings.name === 'New ad group');
                goToContentAds = data.settings.name === 'New ad group';
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.discardSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;
        $scope.errors = {};
        api.adGroupSettings.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.defaultSettings = data.defaultSettings;
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
        var prevAdGroup = $scope.adGroup.id,
            stateActive = constants.adGroupSourceSettingsState.ACTIVE;
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;

        api.adGroupSettings.save($scope.settings).then(
            function (data) {
                var currAdGroup = $scope.adGroup.id,
                    adGroupToEdit = null,
                    status = getAdGroupStatus($scope.settings);
                $scope.errors = {};
                if (prevAdGroup !== currAdGroup) {
                    adGroupToEdit = $scope.getAdGroup(prevAdGroup);
                    adGroupToEdit.name = data.settings.name;
                    adGroupToEdit.state = data.settings.state === stateActive ? 'enabled' : 'paused';
                } else {
                    $scope.settings = data.settings;
                    $scope.defaultSettings = data.defaultSettings;
                    $scope.actionIsWaiting = data.actionIsWaiting;

                    $scope.updateAccounts(data.settings.name, data.settings.state, status);
                    $scope.updateBreadcrumbAndTitle();
                    $scope.setAdGroupPaused(
                        $scope.settings.state === constants.adGroupSettingsState.INACTIVE
                    );
                }

                $scope.saveRequestInProgress = false;
                $scope.saved = true;

                if ($scope.user.showOnboardingGuidance && goToContentAds) {
                    $timeout(function () {
                        $state.go('main.adGroups.adsPlus', {id: $scope.settings.id});
                    }, 100);
                }
            },
            function (data) {
                $scope.errors = data;
                $scope.saveRequestInProgress = false;
                $scope.saved = false;
            }
        );
    };

    function getDeviceItemByValue (devices, value) {
        var result;

        devices.forEach(function (item) {
            if (item.value === value) {
                result = item;
            }
        });

        return result;
    }

    $scope.isDefaultTargetDevices = function () {
        var isDefault = true;
        var item, defaultItem;

        options.adTargetDevices.forEach(function (option) {
            item = getDeviceItemByValue($scope.settings.targetDevices, option.value);
            defaultItem = getDeviceItemByValue($scope.defaultSettings.targetDevices, option.value);

            if (item.checked !== defaultItem.checked) {
                isDefault = false;
            }
        });

        return isDefault;
    };

    $scope.isDefaultTargetRegions = function () {
        var result = true;

        if ($scope.settings.targetRegions.length !== $scope.defaultSettings.targetRegions.length) {
            return false;
        }

        $scope.settings.targetRegions.forEach(function (region) {
            if ($scope.defaultSettings.targetRegions.indexOf(region) === -1) {
                result = false;
            }
        });

        return result;
    };

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

    if (!$scope.adGroup.archived) {
        $scope.getSettings($state.params.id);
    }
}]);
