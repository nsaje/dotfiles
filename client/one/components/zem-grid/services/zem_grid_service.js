/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridConstants', 'zemGridParser', 'zemGridObject', function ($q, zemGridConstants, zemGridParser, zemGridObject) { // eslint-disable-line max-len

    function loadGrid (dataSource) {
        var deferred = $q.defer();
        dataSource.getMetaData().then(
            function (data) {
                var grid = new zemGridObject.createInstance();
                grid.header.columns = data.columns;
                grid.meta.source = dataSource;
                deferred.resolve(grid);
            }
        );
        return deferred.promise;
    }

    function loadData (grid, row, size) {
        var breakdown = null;
        if (row) breakdown = row.data;
        var deferred = $q.defer();
        grid.ui.loading = true;
        grid.meta.source.getData(breakdown, size).then(
            function (data) {
                if (breakdown) {
                    zemGridParser.parseInplace(grid, row, data);
                } else {
                    zemGridParser.parse(grid, data);
                }
                deferred.resolve();
            }
        ).finally(function () {
            grid.ui.loading = false;
        });
        return deferred.promise;
    }

    function setRowCollapsed (grid, gridRow, collapsed) {
        gridRow.collapsed = collapsed;
        var idx = grid.body.rows.indexOf(gridRow);
        while (++idx < grid.body.rows.length) {
            var child = grid.body.rows[idx];
            if (child.level <= gridRow.level) break;
            child.visible = !gridRow.collapsed && !child.parent.collapsed;
        }
    }

    function toggleCollapse (grid, gridRow) {
        setRowCollapsed(grid, gridRow, !gridRow.collapsed);
    }

    function toggleCollapseLevel (grid, level) {
        var collapsed = null;
        for (var i = 0; i < grid.body.rows.length; ++i) {
            var row = grid.body.rows[i];
            if (row.level === level) {
                if (collapsed === null)
                    collapsed = !row.collapsed;
                setRowCollapsed(grid, row, collapsed);
            }
        }
    }

    return {
        loadGrid: loadGrid,
        loadData: loadData,

        // TODO: Move to separate service (interaction service)
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
    };
}]);
