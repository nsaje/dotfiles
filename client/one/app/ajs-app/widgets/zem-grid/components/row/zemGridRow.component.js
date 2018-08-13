angular
    .module('one.widgets')
    .directive('zemGridRow', function(zemGridConstants, NgZone) {
        var DUMMY_ROW = {
            entity: constants.entityType.ACCOUNT,
            level: zemGridConstants.gridRowLevel.BASE,
            type: zemGridConstants.gridRowType.STATS,
            data: {stats: {}},
            dummy: true,
        };

        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                index: '=',
                grid: '=',
            },
            template: require('./zemGridRow.component.html'),
            link: function(scope, element) {
                var grid = scope.ctrl.grid;
                var pubsub = scope.ctrl.grid.meta.pubsub;
                updateRow();
                pubsub.register(
                    pubsub.EVENTS.BODY_ROWS_UPDATED,
                    scope,
                    updateRow
                );
                pubsub.register(
                    pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                    scope,
                    function() {
                        NgZone.runOutsideAngular(function() {
                            var updated = updateRow();
                            if (updated) scope.$digest();
                        });
                    }
                );

                function updateRow() {
                    if (grid.meta.loading) {
                        // [rendering optimization] Use dummy row if grid is loading
                        scope.ctrl.row = DUMMY_ROW;
                        return;
                    }
                    var visibleRows = grid.body.visibleRows.length;
                    if (!visibleRows || visibleRows <= scope.ctrl.index) {
                        // Ignore when there is no visibleRows or row is outside of bounds (no needed)
                        // data updated -> this row will be destroyed
                        return;
                    }

                    // Find appropriate row to be used based on circular row indexes inside visible rows collection
                    var firstRowPos = Math.floor(
                        grid.body.ui.scrollTop /
                            zemGridConstants.gridBodyRendering.ROW_HEIGHT
                    );
                    var firstRowIndex = firstRowPos % grid.body.ui.numOfRows;
                    var rowPos = firstRowPos - firstRowIndex + scope.ctrl.index;
                    if (rowPos < firstRowPos) rowPos += grid.body.ui.numOfRows;

                    // Be sure no to fall out -> renderedRows <= visibleRows
                    if (rowPos >= visibleRows) rowPos -= grid.body.ui.numOfRows;
                    var row = scope.ctrl.grid.body.visibleRows[rowPos];
                    if (row && scope.ctrl.row !== row) {
                        scope.ctrl.row = row;
                        element.css(row.style);
                        return true;
                    }
                    return false;
                }
            },
            controller: function($scope, zemGridConstants) {
                $scope.constants = zemGridConstants;
                var vm = this;
                vm.getRowClass = getRowClass;

                function getRowClass() {
                    if (!vm.row) return [];

                    var classes = [];
                    classes.push('level-' + vm.row.level);
                    if (
                        vm.row.level ===
                        vm.grid.meta.dataService.getBreakdownLevel()
                    )
                        classes.push('level-last');
                    if (vm.row.type === zemGridConstants.gridRowType.BREAKDOWN)
                        classes.push('breakdown');
                    if (vm.row.data.archived) classes.push('archived');
                    return classes;
                }
            },
        };
    });
