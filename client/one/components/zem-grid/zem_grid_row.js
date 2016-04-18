/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridRow', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row.html',
        controller: ['$scope', 'zemGridConstants', 'zemGridUtil', function ($scope, zemGridConstants, zemGridUtil) {
            $scope.constants = zemGridConstants;

            this.loadMore = function () {
                zemGridUtil.loadMore(this.grid, this.row, 5);
            };

            this.getRowClass = function () {
                var classes = [];
                classes.push('level-' + this.row.level);

                if (this.row.level === this.grid.meta.levels) {
                    classes.push('level-last');
                }
                return classes;
            };
        }],
    };
}]);
