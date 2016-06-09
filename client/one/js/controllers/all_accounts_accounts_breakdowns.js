/* globals oneApp */

oneApp.controller('AllAccountsAccountsBreakdownsCtrl', ['$scope', '$timeout', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, $timeout, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line
    $scope.dataSource = createDataSource();

    // GridApi is defined by zem-grid in initialization, therefor
    // it will be available in the next cycle; postpone initialization using $timeout
    $scope.gridApi = undefined;
    $timeout(initializeGridApi, 0);

    function initializeGridApi () {
        // TODO: Initialize GridApi listeners
    }

    function createDataSource () {
        // Temporary workaround for retrieving columns defined in original controller
        var metadata = zemDataSourceEndpoints.getControllerMetaData($scope, 'AllAccountsAccountsCtrl');
        var endpoint = zemDataSourceEndpoints.createAllAccountsEndpoint(metadata);
        var dataSource = zemDataSourceService.createInstance(endpoint);
        dataSource.setDateRange($scope.dateRange, false);
        return dataSource;
    }

    $scope.dataSource.onLoad($scope, function (event, breakdown) {
        var rows = breakdown.rows;
        // TODO: name_link not used at the moment (breakdown column - 1st - not yet supported)
        if (breakdown.level === 1) {
            rows.map(function (row) {
                row.stats.name_link = { // eslint-disable-line camelcase
                    text: row.stats.name,
                    state: $scope.getDefaultAccountState(),
                    id: row.stats.id,
                };
                return row;
            });
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }
        $scope.dataSource.setDateRange(newValue, true);
    });
}]);
