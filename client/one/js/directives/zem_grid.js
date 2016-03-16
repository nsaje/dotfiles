/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGrid', ['config', 'zemDataSourceService', function (config, zemDataSourceService) {

    var GridRowType = {
        STATS: 1,
        BREAKDOWN: 2,
    };

    function GridRow (type, level, data) {
        this.type = type;
        this.level = level;
        this.data = data;

        this.parent = null;
        this.collapsed = false;
        this.visible = true;
    }

    return {
        restrict: 'E',
        scope: {
            // TODO: bindings
        },
        templateUrl: '/partials/zem_grid.html',
        controller: ['$scope', function ($scope) {

            $scope.dataSource = new zemDataSourceService();
            $scope.config = config;
            $scope.GridRowType = GridRowType;


            $scope.rows = [];
            $scope.columns = ['Name'];
            for (var i = 0; i < 8; ++i) $scope.columns.push('Stat ' + (i + 1));

            $scope.load = function () {
                $scope.dataSource.fetch().then(
                    function (breakdown) {
                        var totalDataRow = breakdown.rows[0];
                        var totalRow = new GridRow(GridRowType.STATS, 0, totalDataRow);
                        $scope.rows = $scope.parseBreakdown(totalRow, totalDataRow.breakdown);
                        $scope.rows.push(totalRow);
                    }
                );
            };

            $scope.loadMore = function (row, size) {
                $scope.dataSource.fetch(row.data, size).then(
                    function (breakdown) {
                        var rows = $scope.parseBreakdown(row, breakdown);
                        var idx = $scope.rows.indexOf(row);
                        rows.pop();
                        $scope.rows.splice.apply($scope.rows, [idx, 0].concat(rows));
                    }
                );
            };

            $scope.parseBreakdown = function (parentGridRow, breakdown) {
                var rows = [];
                var level = breakdown.level;

                breakdown.rows.forEach(function (dataRow) {
                    var gridRow = new GridRow(GridRowType.STATS, level, dataRow);
                    gridRow.parent = parentGridRow;
                    rows.push(gridRow);
                    if (dataRow.breakdown) {
                        rows = rows.concat($scope.parseBreakdown(gridRow, dataRow.breakdown));
                    }
                });

                var gridRow = new GridRow(GridRowType.BREAKDOWN, level, breakdown);
                gridRow.parent = parentGridRow;
                rows.push(gridRow);

                return rows;
            };

            $scope.toggleCollapse = function (gridRow) {
                gridRow.collapsed = !gridRow.collapsed;

                var idx = this.rows.indexOf(gridRow);
                while (++idx < this.rows.length) {
                    var child = this.rows[idx];
                    if (child.level <= gridRow.level) break;
                    child.visible = !gridRow.collapsed && !child.parent.collapsed;
                }
            };

            // TODO: move to filter
            $scope.getRowClass = function (row) {
                var classes = [];
                classes.push('level-' + row.level);

                if (row.level === $scope.dataSource.breakdowns.length) {
                    classes.push('level-last');
                }

                return classes;
            };

            $scope.load();

            // TODO: move to development controller
            $scope.DEBUG_BREAKDOWNS = {'ad_group': true, 'age': true, 'sex': false, 'date': true};
            $scope.DEBUG_APPLY_BREAKDOWN = function () {
                var breakdowns = [];
                angular.forEach($scope.DEBUG_BREAKDOWNS, function (value, key) {
                    if (value) breakdowns.push(key);
                });
                $scope.dataSource.breakdowns = breakdowns;
                $scope.dataSource.defaultPagination = [2, 3, 5, 7];
                $scope.load();
            };

        }],
    };
}]);
