oneApp.controller('AdGroupNetworksCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.getTableData = function (id) {
        api.adGroupNetworksTable.get(id).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.getTableData($state.params.id);
}]);
