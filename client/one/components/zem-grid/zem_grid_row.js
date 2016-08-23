/* globals oneApp */
'use strict';

oneApp.directive('zemGridRow', ['zemGridConstants', function (zemGridConstants) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            index: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row.html',
        link: function (scope, element) {
            var grid = scope.ctrl.grid;
            var pubsub = scope.ctrl.grid.meta.pubsub;

            updateRow();
            pubsub.register(pubsub.EVENTS.BODY_ROWS_UPDATED, scope, updateRow);
            pubsub.register(pubsub.EVENTS.BODY_VERTICAL_SCROLL, scope, function () {
                var updated = updateRow();
                if (updated) scope.$digest();
            });

            function updateRow () {
                var visibleRows = grid.body.visibleRows.length;
                if (!visibleRows) {
                    // Ignore when there is no visibleRows (data updated -> this row will be destroyed)
                    return;
                }

                var renderedRows = zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE
                    + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;

                // Find appropriate row to be used based on circular row indexes inside visible rows collection
                var firstRowPos = Math.floor(grid.body.ui.scrollTop / zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                var firstRowIndex = firstRowPos % renderedRows;
                var rowPos = (firstRowPos - firstRowIndex) + scope.ctrl.index;
                if (rowPos < firstRowPos) rowPos += renderedRows;

                // Be sure no to fall out -> renderedRows <= visibleRows
                if (rowPos >= visibleRows) rowPos -= renderedRows;
                var row = scope.ctrl.grid.body.visibleRows[rowPos];
                if (scope.ctrl.row !== row) {
                    scope.ctrl.row = row;
                    element.css(row.style);
                    return true;
                }
                return false;
            }
        },
        controller: ['$scope', 'zemGridConstants', 'zemGridUIService',
            function ($scope, zemGridConstants, zemGridUIService) {
                $scope.constants = zemGridConstants;
                var vm = this;
                vm.getRowClass = getRowClass;

                function getRowClass () {
                    var classes = [];
                    classes.push('level-' + vm.row.level);
                    if (vm.row.level === vm.grid.meta.dataService.getBreakdownLevel()) classes.push('level-last');
                    if (vm.row.type === zemGridConstants.gridRowType.BREAKDOWN) classes.push('breakdown');
                    if (vm.row.data.archived) classes.push('archived');
                    return classes;
                }
            }],
    };
}]);
