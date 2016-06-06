/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridApiService', [function () {

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
        grid.meta.api.onSelectionChanged(gridRow);
    }

    function getSelectedRows (grid) {
        var selectedData = [];
        grid.body.rows.forEach (function (row) {
            if (row.selected) {
                selectedData.push(row);
            }
        });
        return selectedData;
    }

    function toggleColumnSelection (grid, column) {
        column.
        grid.header.columns = columns;

        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
        grid.meta.api.onColumnSelectionChanged(column);
    }

    function getSelectedColumns (grid) {
        return angular.copy(grid.header.columns);
    }

    function initializeApi (grid) {
        // Initialize Grid API

        // Zem-Grid Getters
        grid.meta.api.getSelectedRows = function () { return getSelectedRows(grid); };
        grid.meta.api.getSelectedColumns = function (){ return getSelectedColumns(grid); };
        grid.meta.api.getCollapsedRows = function (){ return getCollapsedRows(grid); };

        grid.meta.api.selectRow = function (row) {  };
        grid.meta.api.collapseRow = function (row) {  };
        grid.meta.api.selectColumn = function (row) {  };

        // Initialize notification hooks with noops if not provided
        grid.meta.api = grid.meta.api || {};
        grid.meta.api.onSelectionChanged = grid.meta.api.onSelectionChanged || angular.noop;
        grid.meta.api.onColumnSelectionChanged = grid.meta.api.onColumnSelectionChanged || angular.noop;
    }

    return {
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
        toggleSelection: toggleSelection,

        initializeGrid: initializeApi,

        collapseRow: collapseRow,
        selectRow: selectRow,
        selectColumn: selectColumn

        getSelectedRows: getSelectedRows,
        getCollapsedRows: getCollapsedRows,
        getSelectedColumns: getSelectedColumns,
    };
}]);
