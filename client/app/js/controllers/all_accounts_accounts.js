/*globals oneApp*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', 'api', function ($scope, api) {
    $scope.requestInProgress = false;
    $scope.addedName = null;
    $scope.added = null;

    $scope.addAccount = function () {
        $scope.requestInProgress = true;
        $scope.addedName = null;
        $scope.added = null;

        api.account.create().then(
            function (data) {
                $scope.accounts.push({
                    'name': data.name,
                    'id': data.id,
                    'campaigns': []
                });

                $scope.addedName = data.name;
                $scope.added = true;
            },
            function (data) {
                // error
                $scope.added = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };
}]);
