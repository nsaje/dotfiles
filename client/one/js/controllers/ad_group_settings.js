/*globals oneApp,constants,options,moment*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', 'regions', 'zemNavigationService', function ($scope, $state, $q, $timeout, api, regions, zemNavigationService) { // eslint-disable-line max-len
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
    $scope.retargetableAdGroups = [];
    $scope.warnings = {};

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

    $scope.getSettings = function (id) {
        $scope.loadRequestInProgress = true;

        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.defaultSettings = data.defaultSettings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.retargetableAdGroups = data.retargetableAdGroups;
                $scope.warnings = data.warnings;
                $scope.updateWarningText();
                freshSettings.resolve(data.settings.name === 'New ad group');
                goToContentAds = data.settings.name === 'New ad group';
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
        };

        if ($scope.warnings.retargeting !== undefined) {
            $scope.warnings.retargeting.text = 'You have some active media sources that don\'t support retargeting. ' +
               'To start using it please disable/pause these media sources:';
        }

        if ($scope.warnings.endDate !== undefined) {
            $scope.warnings.endDate.text = 'Your campaign has been switched to landing mode. ' +
                'Please add the budget and continue to adjust settings by your needs. ';
                // '<a zem-in-link="{{\'main.campaigns.budget_plus\'}}({id: ' + $scope.warnings.endDate.campaignId + '})">Add budget</a>';
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

        api.adGroupSettings.save($scope.settings).then(
            function (data) {
                var currAdGroup = $scope.adGroup.id;
                $scope.errors = {};
                if (prevAdGroup !== currAdGroup) {
                    zemNavigationService.updateAdGroupCache(prevAdGroup, {
                        name: data.settings.name,
                        state: data.settings.state,
                    });
                } else {
                    $scope.settings = data.settings;
                    $scope.defaultSettings = data.defaultSettings;
                    $scope.actionIsWaiting = data.actionIsWaiting;

                    zemNavigationService.updateAdGroupCache(currAdGroup, {
                        name: data.settings.name,
                        state: data.settings.state,
                        status: status,
                    });
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

    var init = function () {
        if (!$scope.adGroup.archived) {
            $scope.getSettings($state.params.id);
        }
    };

    init();
}]);
