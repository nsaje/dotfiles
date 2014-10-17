/*globals oneApp*/
oneApp.controller('AccountAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.errors = {};
    $scope.requestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.discarded = discarded;
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
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.updateAccounts(data.settings.name);
                $scope.updateBreadcrumbAndTitle();
                $scope.requestInProgress = false;
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

    $scope.archiveAccount = function () {
        api.accountArchive.archive($scope.account.id).then(function () {
            api.navData.list().then(function (accounts) {
                $scope.refreshNavData(accounts);
                $scope.getAccount();
            });
            $scope.getSettings();
        });
    };

    $scope.restoreAccount = function () {
        api.accountArchive.restore($scope.account.id).then(function () {
            api.navData.list().then(function (accounts) {
                $scope.refreshNavData(accounts);
                $scope.getAccount();
            });
            $scope.getSettings();
        });
    };

    $scope.getSettings();
}]);
