/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridConstants', 'zemGridParser', 'zemGridObject', function ($q, zemGridConstants, zemGridParser, zemGridObject) { // eslint-disable-line max-len

    /** DEBUG DATA **/
    var columns = ['Name', 'Short stat', 'Looooogner stat', 'Realy looooooooooong stat',
        'A', 'B', 'C', 'AA', 'BB', 'CC', 'AAA', 'BBB', 'CCC', 'AAAA', 'BBBB',
        'CCCC', 'AAAAA', 'BBBBB', 'CCCCC', 'ZZZZZ'];
    var breakdowns = ['ad_group', 'age', 'date'];
    var columnsWidths = [];
    for (var i = 0; i < columns.length; ++i) columnsWidths.push(0);
    /** END DEBUG DATA **/

    function load (dataSource) {
        var deferred = $q.defer();
        dataSource.getData().then(
            function (data) {
                var grid = new zemGridObject.createInstance();
                grid.header.columns = columns;
                grid.meta.breakdowns = breakdowns;
                grid.meta.levels = breakdowns.length;
                grid.meta.source = dataSource;
                grid.ui.columnWidths = columnsWidths;

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

        // TODO: Move to separate service (toggle service)
        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
    };
}]);
