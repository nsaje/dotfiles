/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGrid', ['config', 'zemGridConstants', 'zemGridUtil', 'zemDataSourceService', function (config, zemGridConstants, zemGridUtil, zemDataSourceService) {
    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=?',
            dataSource: '=?',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', function ($scope) {
            this.broadcastEvent = function (event, data) {
                $scope.$broadcast(event, data);
            };

            if (!$scope.options) {
                $scope.options = {};
            }

            if (!$scope.dataSource) {
                $scope.dataSource = new zemDataSourceService();
            }

            $scope.GridRowType = zemGridConstants.gridRowType;

            $scope.load = function () {
                $scope.dataSource.getData().then(
                    function (data) {
                        $scope.grid = zemGridUtil.parseMetaData();
                        zemGridUtil.parseData($scope.grid, data);

                        var columnsWidths = [];
                        for (var i = 0; i < columns.length; ++i) columnsWidths.push(0);
                        $scope.columnsWidths = columnsWidths;
                    }
                );
            };

            $scope.loadMore = function (row, size) {
                $scope.dataSource.getData(row.data, size).then(
                    function (data) {
                        zemGridUtil.parseDataInplace($scope.grid, row, data);
                    }
                );
            };

            $scope.setRowCollapsed = function (gridRow, collapsed) {
                gridRow.collapsed = collapsed;
                var idx = $scope.grid.body.rows.indexOf(gridRow);
                while (++idx < $scope.grid.body.rows.length) {
                    var child = $scope.grid.body.rows[idx];
                    if (child.level <= gridRow.level) break;
                    child.visible = !gridRow.collapsed && !child.parent.collapsed;
                }
            };

            $scope.toggleCollapse = function (gridRow) {
                $scope.setRowCollapsed(gridRow, !gridRow.collapsed);
            };

            $scope.toggleCollapseLevel = function (level) {
                var collapsed = null;
                for (var i = 0; i < $scope.grid.body.rows.length; ++i) {
                    var row = $scope.grid.body.rows[i];
                    if (row.level === level) {
                        if (collapsed === null)
                            collapsed = !row.collapsed;
                        $scope.setRowCollapsed(row, collapsed);
                    }
                }
            };
            $scope.load();
        }],
    };
}]);
