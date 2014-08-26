/*globals oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', 'api', function ($scope, api) {
    $scope.addAccount = function () {
        api.account.create().then(
            function (data) {
                $scope.accounts.push({
                    'name': data.name,
                    'id': data.id,
                    'campaigns': []
                });
            },
            function (data) {
                // error
                return;
            }
        );
    };
}]);
