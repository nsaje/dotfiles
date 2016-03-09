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

            $scope.getMoreData = function (row){
            };
            // TODO: move to filter/template
            $scope.getRowClass = function (row) {
                switch (row.options.level) {
                    case 0: return 'level-0';
                    case 1: return 'level-1';
                    case 2: return 'level-2';
                    case 3: return 'level-3';
                    default: return 'level-3';
                }
            };
        }],
    };
}]);
