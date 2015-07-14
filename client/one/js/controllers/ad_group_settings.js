/*globals oneApp,constants*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', 'api', 'regions', function ($scope, $state, api, regions) {
    $scope.settings = {};
    $scope.sourcesWithoutDMASupport = [];
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.regions = regions;
    $scope.alerts = [];
    $scope.saveRequestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;

    // isOpen has to be an object property instead
    // of being directly on $scope because
    // datepicker-popup directive creates a new child
    // scope which breaks two-way binding in that case
    // https://github.com/angular/angular.js/wiki/Understanding-Scopes
    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};

    $scope.closeAlert = function(index) {
        $scope.alerts.splice(index, 1);
    };

    $scope.openDatePicker = function (type) {
        if (type === 'startDate') {
            $scope.startDatePicker.isOpen = true;
        } else if (type === 'endDate') {
            $scope.endDatePicker.isOpen = true;
        }
    };

    var setSourcesWithoutDMASupport = function(adGroupSources) {
        $scope.sourcesWithoutDMASupport = [];
        if(!adGroupSources) {
            return;
        }
        
        for (var source, i=0; i < adGroupSources.length; i++) {
            source = adGroupSources[i];
            if (source.sourceState === constants.adGroupSourceSettingsState.ACTIVE && !source.supportsDMATargeting) {
                $scope.sourcesWithoutDMASupport.push(source.sourceName);
            }
        }
    };

    $scope.getSettings = function (id) {
        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                setSourcesWithoutDMASupport(data.adGroupSources);
                $scope.setAdGroupPaused($scope.settings.state === constants.adGroupSettingsState.INACTIVE);
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
                setSourcesWithoutDMASupport(data.adGroupSources);
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
                $scope.updateAccounts(data.settings.name);
                $scope.updateBreadcrumbAndTitle();
                $scope.saveRequestInProgress = false;
                $scope.saved = true;
                $scope.setAdGroupPaused($scope.settings.state === constants.adGroupSettingsState.INACTIVE);
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

    if (!$scope.adGroup.archived) {
        $scope.getSettings($state.params.id);
    }
}]);
