/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemGrid', ['config', 'zemDataSourceService', '$window', function (config, zemDataSourceService, $window) {
    return {
        restrict: 'E',
        scope: {
            //dataSource: '=zemDataSource',
        },
        templateUrl: '/partials/zem_grid.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {

            $scope.dataSource = new zemDataSourceService();
            $scope.config = config;
            $scope.constants = constants;
        }],
    };
}]);
