/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridConstants', 'zemGridParser', 'zemGridObject', function ($q, zemGridConstants, zemGridParser, zemGridObject) { // eslint-disable-line max-len

    var columnWidths = getInitialColumnWidths();

    function loadGrid (dataSource) {
        var deferred = $q.defer();
        dataSource.getMetaData().then(
            function (data) {
                var grid = new zemGridObject.createInstance();
                grid.header.columns = data.columns;
                grid.meta.source = dataSource;
                grid.ui.columnWidths = columnWidths;
                deferred.resolve(grid);
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

    function getRowClass (grid, row) {
        var classes = [];
        classes.push('level-' + row.level);

        if (row.level === grid.meta.source.selectedBreakdown.length) {
            classes.push('level-last');
        }
        return classes;
    }

    function getCellStyle (grid, cellIndex) {
        var width = 'auto';
        if (grid.ui.columnWidths[cellIndex]) {
            width = grid.ui.columnWidths[cellIndex] + 'px';
        }
        return {'min-width': width};
    }

    function getInitialColumnWidths () {
        // FIXME: if columnWidth ref changes, it does not work anymore when grid is reloaded (ie. submit new breakdown)
        // ==> it is not possible to generate this array when grid is loading -- load()
        var columnsWidths = [];
        for (var i = 0; i < 50; ++i) columnsWidths.push(20);
        return columnsWidths;
    }


    return {
        loadGrid: loadGrid,
        loadData: loadData,

        // TODO: Move to separate service (interaction service)
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,

        // TODO: Move to separate service (style service)
        getRowClass: getRowClass,
        getCellStyle: getCellStyle,
    };
}]);
