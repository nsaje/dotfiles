/* globals oneApp */

oneApp.controller('DevelopmentGridCtrl', ['$scope', 'zemDataSourceService', function ($scope, zemDataSourceService) {
    $scope.dataSource = zemDataSourceService.createInstance();
}]);
