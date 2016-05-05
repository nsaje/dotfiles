/* globals oneApp */

oneApp.controller('DevelopmentGridCtrl', ['$scope', 'zemDataSourceService', function ($scope, zemDataSourceService) {

    // TODO: bindings with zem-grid and zem-data-source
    $scope.dataSource = zemDataSourceService.createInstance();
}]);
