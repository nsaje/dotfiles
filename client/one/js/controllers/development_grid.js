/* globals oneApp */

oneApp.controller('DevelopmentGridCtrl', ['$scope', 'zemDataSourceService', function ($scope, zemDataSourceService) {
    $scope.dataSource = zemDataSourceService.createInstance();
    $scope.dataSource.breakdowns = ['ad_group', 'age', 'date'];
    $scope.dataSource.defaultPagination = [2, 3, 5, 7];
}]);
