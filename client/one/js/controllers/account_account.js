/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountAccountCtrl', ['$scope', '$state', '$q', 'api', 'zemNavigationService', function ($scope, $state, $q, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.canEditAccount = false;
    $scope.salesReps = [];
    $scope.settings = {};
    $scope.settings.allowedSources = {};
    $scope.saved = false;
    $scope.errors = {};
    $scope.requestInProgress = false;
    $scope.mediaSourcesOrderByProp = 'name';
    $scope.selectedMediaSources = {
        allowed: [], 
        available: []
    };

    $scope.getAllowedMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function (value, key) {
            if (value.allowed) {
                value.value = key;
                this.push(value);
            }
        }, list);
        return list;
    };

    $scope.getAvailableMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function (value, key) {
            if (!value.allowed) {
                value.value = key;
                this.push(value);
            }
        }, list);
        return list;
    };

    $scope.addToAllowedMediaSources =  function () {
        angular.forEach($scope.selectedMediaSources.available, function (value, _) {
            $scope.settings.allowedSources[value].allowed = true;
        });
        $scope.selectedMediaSources.allowed.length = 0;
        $scope.selectedMediaSources.available.length = 0;
    };

    $scope.removeFromAllowedMediaSources = function () {
        angular.forEach($scope.selectedMediaSources.allowed, function (value, _) {
            $scope.settings.allowedSources[value].allowed = false;
        });
        $scope.selectedMediaSources.available.length = 0;
        $scope.selectedMediaSources.allowed.length = 0;
    };

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.accountManagers = data.accountManagers;
                    $scope.salesReps = data.salesReps;
                }
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.saveSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;

        api.accountAgency.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                zemNavigationService.updateAccountCache($state.params.id, {name: data.settings.name});
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.settings.allowedSources = data.allowedSourcesData;
                $scope.saved = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getSettings();
    };

    $scope.init = function () {
        $scope.getSettings();
        $scope.setActiveTab();
    };

    $scope.init();
}]);
