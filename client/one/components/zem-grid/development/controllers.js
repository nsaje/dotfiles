/* globals oneApp */

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess', function () {
        if ($state.is('main.development.grid')
            && !$scope.hasPermission('zemauth.can_access_table_breakdowns_feature')) {
            $state.go('main');
        }
    });
}]);

oneApp.controller('DevelopmentGridCtrl', ['$scope', '$timeout', 'zemDataSourceService', 'zemGridDebugEndpoint', function ($scope, $timeout, zemDataSourceService, zemGridDebugEndpoint) { // eslint-disable-line max-len
    $scope.dataSource = zemDataSourceService.createInstance(zemGridDebugEndpoint.createEndpoint());

    $scope.gridOptions = {
        enableSelection: true,
        enableTotalsSelection: true,
        maxSelectedRows: 3,
    };

    // GridApi is defined by zem-grid in initialization, therefor
    // it will be available in the next cycle; postpone initialization using $timeout
    $scope.gridApi = undefined;
    $timeout(initializeGridApi, 0);

    function initializeGridApi () {
        // Initialize GridApi listeners
        $scope.gridApi.onRowsSelectionChanged($scope, function () {
            console.log($scope.gridApi.getSelectedRows()); // eslint-disable-line
        });
    }
}]);

