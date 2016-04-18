/* globals oneApp */
'use strict';

oneApp.factory('zemGridUtil', ['$q', 'zemGridConstants', function ($q, zemGridConstants) { // eslint-disable-line max-len

    var columns = ['Name', 'Short stat', 'Looooogner stat', 'Realy looooooooooong stat',
        'A', 'B', 'C', 'AA', 'BB', 'CC', 'AAA', 'BBB', 'CCC', 'AAAA', 'BBBB',
        'CCCC', 'AAAAA', 'BBBBB', 'CCCCC', 'ZZZZZ'];

    var breakdowns = ['ad_group', 'age', 'date'];

    // TODO: Refactor - move to appropriate place
    var columnsWidths = [];
    for (var i = 0; i < columns.length; ++i) columnsWidths.push(0);

    function load (dataSource) {
        var deferred = $q.defer();
        dataSource.getData().then(
            function (data) {
                var grid = {
                    header: {},
                    body: {},
                    footer: {},
                    meta: {
                        breakdowns: breakdowns,
                        levels: breakdowns.length,
                        source: dataSource,
                    },
                    ui: {
                        columnWidths: columnsWidths,
                    },
                };
                parseData(grid, data);
                deferred.resolve(grid);
            }
        );

        return deferred.promise;
    }

    function loadMore (grid, row, size) {
        var deferred = $q.defer();
        grid.meta.source.getData(row.data, size).then(
            function (data) {
                parseDataInplace(grid, row, data);
                deferred.resolve();
            }
        );

        return deferred.promise;
    }

    function parseData (grid, data) {
        // Level 0 -> total data and level 1 breakdown
        var totals = data.rows[0];
        var breakdown = totals.breakdown;

        grid.footer = {type: zemGridConstants.gridRowType.STATS, level: 0, data: totals, visible: true};
        grid.body.rows = parseBreakdown(null, breakdown);
    }

    function parseDataInplace (grid, row, data) {
        var rows = parseBreakdown(row.parent, data);
        var idx = rows.indexOf(row);
        rows.pop();
        grid.body.rows.splice.apply(grid.body.rows, [idx, 0].concat(rows));
    }

    function parseBreakdown (parent, breakdown) {
        var rows = [];
        var level = breakdown.level;

        breakdown.rows.forEach(function (data) {
            var row = {
                type: zemGridConstants.gridRowType.STATS,
                level: level,
                data: data,
                parent: parent,
                visible: true,
                collapsed: false,
            };
            rows.push(row);
            if (data.breakdown) {
                var breakdownRows = parseBreakdown(row, data.breakdown);
                rows = rows.concat(breakdownRows);
            }
        });

        var row = {
            type: zemGridConstants.gridRowType.BREAKDOWN,
            level: level,
            data: breakdown,
            parent: parent,
            visible: true,
        };
        rows.push(row);

        return rows;
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
                setRowCollapsed(row, collapsed);
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
