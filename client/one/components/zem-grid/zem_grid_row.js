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
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row.html',
        link: function (scope, element) {
            scope.$watch('ctrl.row.style', function (style) {
                element.css(style);
            });
        },
        controller: ['$scope', 'zemGridConstants', 'zemGridService', 'zemGridUIService',
            function ($scope, zemGridConstants, zemGridService, zemGridUIService) {
                $scope.constants = zemGridConstants;

                this.loadMore = function (size) {
                    if (!size)
                    {
                        size = this.row.data.pagination.count - this.row.data.pagination.to;
                    }
                    zemGridService.loadData(this.grid, this.row, size).then(function () {
                        $scope.ctrl.pubsub.notify($scope.ctrl.pubsub.EVENTS.ROWS_UPDATED);
                    });
                };

                this.getRowClass = function () {
                    return zemGridUIService.getRowClass(this.grid, this.row);
                };
            }],
    };
}]);
