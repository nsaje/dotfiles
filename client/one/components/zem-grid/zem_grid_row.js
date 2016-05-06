/* globals oneApp */
'use strict';

oneApp.directive('zemGridRow', [function () {

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
        controller: ['$scope', 'zemGridConstants', 'zemGridService',
            function ($scope, zemGridConstants, zemGridService) {
                $scope.constants = zemGridConstants;

                this.loadMore = function () {
                    zemGridService.loadMore(this.grid, this.row, 5);
                };

                this.getRowClass = function () {
                    return zemGridService.getRowClass(this.grid, this.row);
                };
            }],
    };
}]);
