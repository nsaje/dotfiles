/* globals oneApp */
'use strict';

oneApp.factory('zemGridParser', ['$filter', 'zemGridConstants', 'zemGridObject', function ($filter, zemGridConstants, zemGridObject) { // eslint-disable-line max-len

    //
    // Service responsible for parsing Breakdown data (tree) to Grid rows
    // It flattens tree so that Grid is functioning on rows[] array.
    //

    function parseMetaData (grid, metadata) {
        grid.meta.data = metadata;
        grid.header.columns = metadata.columns.map(function (data) {
            return zemGridObject.createColumn(data);
        });
    }

    function parse (grid, data) {
        if (data.level > 0) throw 'Inplace parsing not supported yet.';

        if (data.breakdown) {
            grid.footer.row = zemGridObject.createRow(zemGridConstants.gridRowType.FOOTER, data, 0);
            grid.body.rows = parseBreakdown(grid, null, data.breakdown);
        } else {
            grid.body.rows = [];
            grid.footer.row = null;
        }
    }

    function parseBreakdown (grid, parent, breakdown) {
        var rows = [];
        var level = breakdown.level;

        breakdown.rows.forEach(function (data) {
            var row = zemGridObject.createRow(zemGridConstants.gridRowType.STATS, data, level, parent);
            rows.push(row);
            if (data.breakdown) {
                var breakdownRows = parseBreakdown(grid, row, data.breakdown);
                rows = rows.concat(breakdownRows);
            }
        });

        if (!breakdown.pagination.complete || breakdown.pagination.count === 0) {
            // Add breakdown row only if there is more data to be loaded
            // OR there is not data at all (to show empty msg)
            var row = createBreakdownRow(grid, breakdown, parent);
            rows.push(row);
        }

        return rows;
    }

    function createBreakdownRow (grid, breakdown, parent) {
        var row = zemGridObject.createRow(zemGridConstants.gridRowType.BREAKDOWN, breakdown, breakdown.level, parent);

        // TODO: refactor (move to virtual scroll functionality)
        // HACK: Empty stats for render optimizations (ng-repeat, ng-switch)
        var emptyStats = {};
        grid.meta.data.columns.forEach(function (col) {
            emptyStats[col.field] = {};
        });
        row.data.stats = emptyStats;
        return row;
    }

    return {
        parse: parse,
        parseMetaData: parseMetaData,
    };
}]);
