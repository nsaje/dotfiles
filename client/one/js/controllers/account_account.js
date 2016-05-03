/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountAccountCtrl', ['$scope', '$state', '$q', 'api', 'zemNavigationService', function ($scope, $state, $q, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.canEditAccount = false;

    $scope.settings = {};
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.saved = false;
    $scope.errors = {};
    $scope.requestInProgress = false;

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;

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
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                zemNavigationService.updateAccountCache($state.params.id, {name: data.settings.name});
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
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
