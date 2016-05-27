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
        link: function (scope, element) {
            scope.$watch('ctrl.row.style', function (style) {
                element.css(style);
            });
        },
        controller: ['$scope', 'zemGridConstants', 'zemGridUIService',
            function ($scope, zemGridConstants, zemGridUIService) {
                $scope.constants = zemGridConstants;

                this.loadMore = function (size) {
                    if (!size) {
                        size = this.row.data.pagination.count - this.row.data.pagination.limit;
                    }
                    this.grid.meta.service.loadData(this.row, size);
                };

                this.getRowClass = function () {
                    return zemGridUIService.getRowClass(this.grid, this.row);
                };
            }],
    };
}]);
