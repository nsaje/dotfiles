/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridConstants', 'zemGridParser', 'zemGridObject', function ($q, zemGridConstants, zemGridParser, zemGridObject) { // eslint-disable-line max-len

    function load (dataSource) {
        var deferred = $q.defer();
        dataSource.getData().then(
            function (data) {
                var grid = new zemGridObject.createInstance();
                grid.header.columns = data.meta.columns;
                grid.meta.source = dataSource;
                grid.meta.breakdowns = dataSource.breakdowns;
                grid.meta.levels = dataSource.breakdowns.length;

                zemGridParser.parse(grid, data);
                deferred.resolve(grid);
            }
        );

        return deferred.promise;
    }

    function loadMore (grid, row, size) {
        var deferred = $q.defer();
        grid.meta.source.getData(row.data, size).then(
            function (data) {
                zemGridParser.parseInplace(grid, row, data);
                deferred.resolve();
            }
        );
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
        load: load,
        loadMore: loadMore,

        // TODO: Move to separate service (interaction service)
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
    };
}]);
