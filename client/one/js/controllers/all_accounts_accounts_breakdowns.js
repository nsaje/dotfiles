/* globals oneApp */
oneApp.controller('AllAccountsAccountsBreakdownsCtrl', ['$scope', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line
    var endpoint = zemDataSourceEndpoints.createAllAccountsEndpoint();
    $scope.dataSource = zemDataSourceService.createInstance(endpoint);

    $scope.configureDataSource = function () {
        // TODO: propagate configuration to automatically request Grid reload
        $scope.dataSource.config = {
            start_date: $scope.dateRange.startDate.format('YYYY-MM-DD'),
            end_date: $scope.dateRange.endDate.format('YYYY-MM-DD'),
            order: '-clicks', // TODO: support ordering
        };
    };

    $scope.dataSource.onLoad($scope, function (event, breakdown) {
        var rows = breakdown.rows;
        // TODO: name_link not used at the moment (breakdown column - 1st - not yet supported)
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

    $scope.configureDataSource();
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }
        $scope.configureDataSource();
    });
}]);
