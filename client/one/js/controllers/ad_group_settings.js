/*globals oneApp,constants,options,moment*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', 'regions', 'zemNavigationService', function ($scope, $state, $q, $timeout, api, regions, zemNavigationService) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.loadRequestInProgress = true;
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.regions = regions;
    $scope.options = options;
    $scope.constants = constants;
    $scope.alerts = [];
    $scope.saveRequestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.minEndDate = new Date();
    $scope.retargetableAdGroups = [];
    $scope.warnings = {};
    $scope.canArchive = false;
    $scope.canRestore = false;

    // isOpen has to be an object property instead
    // of being directly on $scope because
    // datepicker-popup directive creates a new child
    // scope which breaks two-way binding in that case
    // https://github.com/angular/angular.js/wiki/Understanding-Scopes
    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};

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

    $scope.getSettings = function (id) {
        $scope.loadRequestInProgress = true;

        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.settings = data.settings;
                $scope.defaultSettings = data.defaultSettings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.retargetableAdGroups = data.retargetableAdGroups;
                $scope.warnings = data.warnings;
                $scope.updateWarningText();

                // TODO
                $scope.settings.gaTrackingType = 1;
            },
            function () {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.updateWarningText = function () {
        if (!$scope.warnings) {
            return;
        }

        if ($scope.warnings.retargeting !== undefined) {
            $scope.warnings.retargeting.text = 'You have some active media sources that ' +
                'don\'t support retargeting. ' +
                'To start using it please disable/pause these media sources:';
            $scope.warnings.retargeting.sourcesText = $scope.warnings.retargeting.sources.join(', ');
        }

        if ($scope.warnings.endDate !== undefined) {
            $scope.warnings.endDate.text = 'Your campaign has been switched to landing mode. ' +
                'Please add the budget and continue to adjust settings by your needs. ';
        }
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
            function () {
                // error
                $scope.saveRequestInProgress = false;
                return;
            }
        );
    };

    $scope.saveSettings = function () {
        var prevAdGroup = $scope.adGroup.id;

        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;

        zemNavigationService.notifyAdGroupReloading($state.params.id, true);

        api.adGroupSettings.save($scope.settings).then(
            function (data) {
                var currAdGroup = $scope.adGroup.id;
                $scope.errors = {};
                if (prevAdGroup === currAdGroup) {
                    $scope.settings = data.settings;
                    $scope.defaultSettings = data.defaultSettings;
                    $scope.actionIsWaiting = data.actionIsWaiting;
                }

                zemNavigationService.reloadAdGroup($state.params.id);
                $scope.saveRequestInProgress = false;
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.saveRequestInProgress = false;
                $scope.saved = false;
                zemNavigationService.notifyAdGroupReloading($state.params.id, false);
            }
        );
    };

    $scope.archiveAdGroup = function () {
        $scope.saveRequestInProgress = true;
        zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, true);
        api.adGroupArchive.archive($scope.adGroup.id).then(function () {
            $scope.refreshPage();
            $scope.saveRequestInProgress = false;
        }, function () {
            zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, false);
            $scope.saveRequestInProgress = false;
        });
    };

    $scope.restoreAdGroup = function () {
        $scope.saveRequestInProgress = true;
        zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, true);
        api.adGroupArchive.restore($scope.adGroup.id).then(function () {
            $scope.refreshPage();
            $scope.saveRequestInProgress = false;
        }, function () {
            zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, false);
            $scope.saveRequestInProgress = false;
        });
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

    $scope.showAutoPilotDailyBudgetInput = function () {
        return $scope.settings.autopilotState === constants.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET;
    };

    $scope.budgetAutopilotOptimizationGoalText = function () {
        var goalName = 'maximum volume';
        options.budgetAutomationGoals.forEach(function (goal) {
            if (goal.value === $scope.settings.autopilotOptimizationGoal) {
                goalName = goal.name;
            }
        });
        return goalName;
    };

    $scope.budgetAutopilotOptimizationCPAGoalText = function () {
        if ($scope.settings.autopilotOptimizationGoal !== constants.campaignGoalKPI.CPA) {
            return '';
        }
        return 'Note: CPA optimization works best when at least 20 conversions have occurred in the past two weeks.';
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

    $scope.refreshPage = function () {
        zemNavigationService.reloadAdGroup($state.params.id);
        $scope.getSettings($state.params.id);
    };

    $scope.getGaTrackingTypeByValue = function (value) {
        var result;
        options.gaTrackingType.forEach(function (type) {
            if (type.value === value) {
                result = type;
                return;
            }
        });

        return result;
    };

    var init = function () {
        $scope.getSettings($state.params.id);
    };

    init();
}]);
