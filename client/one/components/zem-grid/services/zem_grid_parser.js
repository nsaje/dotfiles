/* globals oneApp */
'use strict';

oneApp.factory('zemGridParser', ['$q', 'zemGridConstants', function ($q, zemGridConstants) {

    //
    // Service responsible for parsing Breakdown data (tree) to Grid rows
    // It flattens tree so that Grid is functioning on rows[] array.
    //

    function parse (grid, data) {
        if (data.level > 0) throw 'Inplace parsing not supported yet.';

        if (data.breakdown) {
            grid.footer = {type: zemGridConstants.gridRowType.STATS, level: 0, data: data, visible: true};
            grid.body.rows = parseBreakdown(grid, null, data.breakdown);
        } else {
            grid.body.rows = [];
            grid.footer.stats = null;
        }
    }

    function parseBreakdown (grid, parent, breakdown) {
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
                var breakdownRows = parseBreakdown(grid, row, data.breakdown);
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

        // TODO: refactor (move to virtual scroll functionality)
        // HACK: Empty stats for render optimizations (ng-repeat, ng-switch)
        var emptyStats = {};
        grid.header.columns.forEach(function (col) {
            emptyStats[col.field] = '';
        });
        row.data.stats = emptyStats;
        rows.push(row);

        return rows;
    }

    return {
        parse: parse,
    };
}]);
