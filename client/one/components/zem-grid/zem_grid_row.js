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
        controller: ['$scope', 'zemGridConstants', 'zemGridService',
            function ($scope, zemGridConstants, zemGridService) {
                $scope.constants = zemGridConstants;

                this.loadMore = function () {
                    zemGridService.loadMore(this.grid, this.row, 5).then(function () {
                        $scope.ctrl.pubsub.notify($scope.ctrl.pubsub.EVENTS.ROWS_UPDATED);
                    });
                };

                this.getRowClass = function () {
                    return zemGridService.getRowClass(this.grid, this.row);
                };
            }],
    };
}]);
