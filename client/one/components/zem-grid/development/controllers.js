/* globals oneApp */

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess', function () {
        if ($state.is('main.development.grid') &&
            !$scope.hasPermission('zemauth.can_access_table_breakdowns_development_features')) {
            $state.go('main');
        }
    });
}]);

oneApp.controller('DevelopmentGridCtrl', ['$scope', '$http', '$q', 'zemDataSourceService', 'zemDataSourceDebugEndpoints', function ($scope, $http, $q, zemDataSourceService, zemDataSourceEndpoints) { // eslint-disable-line
    $scope.dataSource = zemDataSourceService.createInstance(zemDataSourceEndpoints.createMockEndpoint());
}]);

