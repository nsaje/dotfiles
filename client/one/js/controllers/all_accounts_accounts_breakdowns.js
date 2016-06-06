/* globals oneApp */
oneApp.controller('AllAccountsAccountsBreakdownsCtrl', ['$scope', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line
    $scope.dataSource = createDataSource();
    $scope.gridApi = {
        onSelectionChanged: function (selectedData) {
            debugger;
            console.log('Selection changed: ' + selectedData);
        },
    };

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
