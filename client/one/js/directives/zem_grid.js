/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemGrid', ['config', 'zemDataSourceService', '$window', function (config, zemDataSourceService, $window) {

    function GridRow (type, level, dataRow) {
        this.dataRow = dataRow;
        this.data = dataRow.data;

        this.level = level;
        this.type = type;

        this.collapsed = false;
        this.visible = true;

        this.parent = null;
    }


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

            $scope.rows = [];

            $scope.load = function () {
                $scope.dataSource.fetchInitial().then(
                    function (breakdown){
                        var totalDataRow = breakdown.rows[0];
                        var totalRow = new GridRow(0, 0, totalDataRow);
                        $scope.rows = $scope.parseBreakdown(totalRow, totalDataRow.breakdown);
                        $scope.rows.push(totalRow);
                    }, function (error) {

                    }
                );
            };

            $scope.loadMore = function (row) {
                $scope.dataSource.fetchMore(row.dataRow).then(
                    function (breakdown){
                        var rows = $scope.parseBreakdown(row, breakdown);
                        var idx = $scope.rows.indexOf(row);
                        rows.pop();
                        $scope.rows.splice.apply($scope.rows, [idx, 0].concat(rows));
                    }, function (error) {

                    }
                );
            };

            $scope.parseBreakdown = function (parentGridRow, breakdown) {
                var rows = [];
                var level = breakdown.level;

                breakdown.rows.forEach (function(dataRow) {
                    var gridRow = new GridRow(0, level, dataRow);
                    gridRow.parent = parentGridRow;
                    rows.push(gridRow);
                    if (dataRow.breakdown) {
                        rows = rows.concat($scope.parseBreakdown(gridRow, dataRow.breakdown));
                    }
                });

                var gridRow = new GridRow(1, level, breakdown);
                gridRow.parent = parentGridRow;
                rows.push(gridRow);

                return rows;
            };

            $scope.toggleCollapse = function (gridRow) {

                var idx = this.rows.indexOf(gridRow);

                gridRow.collapsed = !gridRow.collapsed;

                while (true) {
                    if (idx >= this.rows.length) break;

                    var child = this.rows[++idx];
                    if (child.level <= gridRow.level) break;

                    child.visible = !gridRow.collapsed && !child.parent.collapsed;
                }
            };

            // TODO: move to filter/template
            $scope.getRowClass = function (row) {
                switch (row.level) {
                    case 0: return 'level-0';
                    case 1: return 'level-1';
                    case 2: return 'level-2';
                    case 3: return 'level-3';
                    default: return 'level-3';
                }
            };

            $scope.load();

        }],
    };
}]);
