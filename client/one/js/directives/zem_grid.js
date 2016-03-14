/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemGrid', ['config', 'zemDataSourceService', '$window', function (config, zemDataSourceService, $window) {
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

            this.toggleCollapse = function (gridRow) {

                var idx = this.rows.indexOf(gridRow);

                gridRow.collapsed = !gridRow.collapsed;

                while (true) {
                    if (idx >= this.rows.length) break;

                    var child = this.rows[++idx];
                    if (child.level <= gridRow.level) break;

                    child.visible = !gridRow.collapsed && !child.parent.collapsed;
                }
            };

            function parseData (data) {
                var gridRow = new GridRow(0, 0, data);
                var rows = parseBreakdown(gridRow, data.breakdown);
                rows.push(gridRow);
                return rows;
            }

            function parseBreakdown (parentGridRow, breakdown) {
                var rows = [];
                var level = breakdown.position.length + 1;

                angular.forEach(breakdown.rows, function (row) {
                    var gridRow = new GridRow(0, level, row);
                    gridRow.parent = parentGridRow;
                    rows.push(gridRow);
                    if (row.hasOwnProperty('breakdown')) {
                        rows = rows.concat(parseBreakdown(gridRow, row.breakdown));
                    }
                });

                var gridRow = new GridRow(1, level, breakdown);
                gridRow.parent = parentGridRow;
                rows.push(gridRow);

                return rows;
            }


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

        }],
    };
}]);
