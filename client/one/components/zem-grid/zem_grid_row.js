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
                var vm = this;
                vm.getRowClass = getRowClass;

                function getRowClass () {
                    var classes = [];
                    classes.push('level-' + vm.row.level);
                    if (vm.row.level === vm.grid.meta.service.getBreakdownLevel()) classes.push('level-last');
                    if (vm.row.type === zemGridConstants.gridRowType.BREAKDOWN) classes.push('breakdown');
                    if (vm.row.data.archived) classes.push('archived');
                    return classes;
                }
            }],
    };
}]);
