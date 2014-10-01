/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountBudgetCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.total = 0;
    $scope.spend = 0;
    $scope.available = 0;
    $scope.requestInProgress = true;

    $scope.getBudget = function() {
        $scope.requestInProgress = true;
        api.accountBudget.get($state.params.id).then(
            function (data) {
                $scope.total = data.total;
                $scope.spend = data.spend;
                $scope.available = data.available;
            },
            function (data) {
                // error
                return
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.getBudget();

}]);