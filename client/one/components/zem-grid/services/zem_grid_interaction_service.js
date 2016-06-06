/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridUIService', ['$timeout', 'zemGridConstants', function ($timeout, zemGridConstants) {

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

    function toggleSelection (grid, gridRow) {
        gridRow.selected = !gridRow.selected;

        var selectedData = grid.body.rows
            .filter(function (row) { return row.selected; })
            .map(function (row) { return row.data; });

        grid.meta.api.onSelectionChanged(selectedData);
    }

    return {
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
        toggleSelection: toggleSelection,
    };
}]);
