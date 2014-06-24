oneApp.controller('AdGroupNetworksCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.loadRequestInProgress = false;

    $scope.getTableData = function (id) {
        $scope.loadRequestInProgress = true;

        api.adGroupNetworksTable.get(id).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.getTableData($state.params.id);
}]);
