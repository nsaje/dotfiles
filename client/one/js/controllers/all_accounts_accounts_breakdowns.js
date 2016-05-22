/* globals oneApp */
oneApp.controller('AllAccountsAccountsBreakdownsCtrl', ['$scope', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line
    var endpoint = zemDataSourceEndpoints.createAllAccountsEndpoint();
    $scope.dataSource = zemDataSourceService.createInstance(endpoint);
    $scope.dataSource.onLoad($scope, function (event, breakdown) {
        var rows = breakdown.rows;
        if (breakdown.level == 1) {
            rows.map(function (row) {
                row.stats.name_link = { // eslint-disable-line
                    text: row.stats.name,
                    state: $scope.getDefaultAccountState(),
                    id: row.stats.id,
                };
                return row;
            });
        }
    });
}]);
