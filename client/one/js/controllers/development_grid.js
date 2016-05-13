/* globals oneApp */

oneApp.controller('DevelopmentGridCtrl', ['$scope', '$http','$q', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, $http, $q, zemDataSourceService, zemDataSourceEndpoints) {

    $scope.dataSource = zemDataSourceService.createInstance(zemDataSourceEndpoints.createMockEndpoint());

}]);

oneApp.controller('DevelopmentGridLegacyCtrl', ['$scope', '$controller', '$q', '$timeout', 'zemDataSourceService', 'zemDataSourceEndpoints', function ($scope, $controller, $q, $timeout, zemDataSourceService, zemDataSourceEndpoints) {
    $scope.dataSource = zemDataSourceService.createInstance(zemDataSourceEndpoints.createAllAccountsCachedEndpoint());
    $scope.dataSource.breakdowns = ['account'];

    $scope.dataSource.onLoad($scope, function (event, data) {
        var rows = data.rows;
        if (data.level === 0){
            rows = data.rows[0].breakdown.rows;
        }

        rows.map(function (row) {
            row.stats.name_link = {
                text: row.stats.name,
                state: $scope.getDefaultAccountState(),
                id: row.stats.id,
            };
            return row;
        });
    });
}]);
