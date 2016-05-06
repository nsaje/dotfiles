/* globals oneApp, options */
oneApp.controller('AccountAgencyCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.history = [];
    $scope.requestInProgress = false;

    $scope.getSettings = function (discarded) {
        $scope.requestInProgress = true;
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.history = data.history;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getSettings();
    };

    $scope.archiveAccount = function () {
        if ($scope.canArchive) {
            api.accountArchive.archive($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.restoreAccount = function () {
        if ($scope.canRestore) {
            api.accountArchive.restore($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.getSettings();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
