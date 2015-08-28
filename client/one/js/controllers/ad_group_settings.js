/*globals oneApp,constants,options*/
oneApp.controller('AdGroupSettingsCtrl', ['$scope', '$state', '$q', 'api', 'regions', function ($scope, $state, $q, api, regions) {
    var freshSettings = $q.defer();
    $scope.settings = {};
    $scope.sourcesWithoutDMASupport = [];
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.regions = regions;
    $scope.options = options;
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

    $scope.adGroupHasFreshSettings = function () {
        return freshSettings.promise;
    };
    
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

    var getAdGroupStatus = function (settings) {
        var now = new Date(),
            running0 = settings.state === constants.adGroupSettingsState.ACTIVE,
            running1 = settings.endDate && (now <= moment(settings.endDate).toDate() && moment(settings.startDate).toDate() <= now),
            running2 = !settings.endDate && (moment(settings.startDate).toDate() <= now);
        return running0 && (running1 || running2) ? 'running' : 'stopped';
    };

    $scope.availableRegions = function() {
        // In case the full country and dma list is not given to the user
        // at least show the ones that are selected
        var avRegions = regions.legacy.slice();

        if ($scope.settings.targetRegions) {
            for (var locationCode, found, i=0; i < $scope.settings.targetRegions.length; i++) {
                locationCode = $scope.settings.targetRegions[i];
                found = avRegions.filter(function(lc) { return lc.code === locationCode;});
                if (found.length === 0) {
                    avRegions.push(regions.getByCode(locationCode));
                }
            }
        }

        return avRegions;
    };

    $scope.getSettings = function (id) {
        api.adGroupSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.actionIsWaiting = data.actionIsWaiting;
                setSourcesWithoutDMASupport(data.adGroupSources);
                $scope.setAdGroupPaused($scope.settings.state === constants.adGroupSettingsState.INACTIVE);
                freshSettings.resolve(data.settings.name == 'New ad group');
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
                if (prevAdGroup != currAdGroup) {
                    adGroupToEdit = $scope.getAdGroup(prevAdGroup);
                    adGroupToEdit.name = data.settings.name;
                    adGroupToEdit.state = data.settings.state === stateActive ? 'enabled' : 'paused';
                } else {
                    $scope.settings = data.settings;
                    $scope.actionIsWaiting = data.actionIsWaiting;
                    
                    $scope.updateAccounts(data.settings.name, data.settings.state, status);
                    $scope.updateBreadcrumbAndTitle();
                    $scope.setAdGroupPaused(
                        $scope.settings.state === constants.adGroupSettingsState.INACTIVE
                    );
                }
                

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

    if (!$scope.adGroup.archived) {
        $scope.getSettings($state.params.id);
    }
}]);
