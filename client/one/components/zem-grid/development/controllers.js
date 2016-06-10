/* globals oneApp */

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess', function () {
        if ($state.is('main.development.grid') &&
            !$scope.hasPermission('zemauth.can_access_table_breakdowns_development_features')) {
            $state.go('main');
        }
    });
}]);

oneApp.controller('DevelopmentGridCtrl', ['$scope', '$timeout', 'zemDataSourceService', 'zemDataSourceDebugEndpoints', function ($scope, $timeout, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line max-len
    $scope.dataSource = zemDataSourceService.createInstance(zemDataSourceEndpoints.createMockEndpoint());

    // GridApi is defined by zem-grid in initialization, therefor
    // it will be available in the next cycle; postpone initialization using $timeout
    $scope.gridApi = undefined;
    $timeout(initializeGridApi, 0);

    function initializeGridApi () {
        // TODO: Initialize GridApi listeners
    }
}]);

