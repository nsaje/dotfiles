/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridConstants', 'zemGridParser', 'zemGridUIService', function ($q, zemGridConstants, zemGridParser, zemGridUIService) { // eslint-disable-line max-len

    function loadMetadata (grid) {
        var deferred = $q.defer();
        grid.meta.source.getMetaData().then(
            function (data) {
                grid.header.columns = data.columns;
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);
                deferred.resolve();
            }
        );
        return deferred.promise;
    }

    function loadData (grid, row, size) {
        var breakdown;
        if (row) {
            breakdown = row.data;
        }

        var deferred = $q.defer();
        grid.meta.source.getData(breakdown, size).then(
            function (data) {
                zemGridParser.parse(grid, data);
                deferred.resolve();
            },
            function () { // error
            },
            function (data) { // notify
                zemGridParser.parse(grid, data);
                zemGridUIService.resetUIState(grid);
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }
        ).finally(function () {
            zemGridUIService.resetUIState(grid);
            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
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
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
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
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
    }

    return {
        loadMetadata: loadMetadata,
        loadData: loadData,

        // TODO: Move to separate service (interaction service)
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
    };
}]);
