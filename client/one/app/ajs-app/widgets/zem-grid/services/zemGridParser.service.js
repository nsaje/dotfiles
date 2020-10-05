angular
    .module('one.widgets')
    .factory('zemGridParser', function(
        $filter,
        zemGridConstants,
        zemGridObject
    ) {
        // eslint-disable-line max-len

        //
        // Service responsible for parsing Breakdown data (tree) to Grid rows
        // It flattens tree so that Grid is functioning on rows[] array.
        //

        function parseMetaData(grid, metadata) {
            grid.meta.data = metadata;
            grid.header.columns = metadata.columns.map(createColumn);
        }

        function parse(grid, data) {
            if (data.level > 0) throw 'Inplace parsing not supported yet.';
            if (data.breakdown) {
                grid.body.rows = parseBreakdown(grid, null, data.breakdown);
                grid.body.pagination = data.breakdown.pagination;
                grid.footer.row = createRow(
                    zemGridConstants.gridRowType.STATS,
                    data,
                    0
                );
            } else {
                grid.body.rows = [];
                grid.footer.row = null;
                grid.body.pagination = null;
            }
        }

        function clear(grid) {
            grid.meta.data = null;
            grid.meta.columns = [];
            grid.body.rows = [];
            grid.footer.row = null;
            grid.body.pagination = null;
        }

        function parseBreakdown(grid, parent, breakdown) {
            var rows = [];
            var level = breakdown.level;
            var inGroup =
                parent &&
                (parent.type === zemGridConstants.gridRowType.GROUP ||
                    parent.inGroup);

            breakdown.rows.forEach(function(data) {
                var type = data.group
                    ? zemGridConstants.gridRowType.GROUP
                    : zemGridConstants.gridRowType.STATS;
                var row = createRow(type, data, level, parent);
                row.inGroup = inGroup;

                rows.push(row);
                if (data.breakdown) {
                    var breakdownRows = parseBreakdown(
                        grid,
                        row,
                        data.breakdown
                    );
                    rows = rows.concat(breakdownRows);
                }
            });

            if (
                !breakdown.replaceRows &&
                (!breakdown.pagination.complete ||
                    breakdown.pagination.count === 0)
            ) {
                // Add breakdown row only if there is more data to be loaded
                // OR there is no data at all (to show empty msg)
                var row = createBreakdownRow(grid, breakdown, parent);
                row.inGroup = inGroup;
                rows.push(row);
            }

            return rows;
        }

        function createBreakdownRow(grid, breakdown, parent) {
            var row = createRow(
                zemGridConstants.gridRowType.BREAKDOWN,
                breakdown,
                breakdown.level,
                parent
            );

            // TODO: refactor (move to virtual scroll functionality)
            // HACK: Empty stats for render optimizations (ng-repeat, ng-switch)
            var emptyStats = {};
            grid.meta.data.columns.forEach(function(col) {
                emptyStats[col.field] = {};
            });
            row.data.stats = emptyStats;
            return row;
        }

        function createRow(type, data, level, parent) {
            // Create row - try to reuse row if already crated
            //  - row can already have some data used by different services (e.g. collapse)
            //  - it is a bit more efficient then to re-create row objects through sequential requests

            // (optional) FIXME For the simplicity we save (cache) row instance into the data itself.
            // This creates circular dependency, which should not cause problems, but it can be avoided
            // with modifying data source to create unique keys that can be used here for storage
            if (!data.row) {
                var row = zemGridObject.createRow(type, data, level, parent);
                if (parent && (parent.collapsed || !parent.visible)) {
                    // Hide row if parent is collapsed or not visible
                    row.visible = false;
                }
                data.row = row;
            }

            return data.row;
        }

        function createColumn(data) {
            // Create column - try to reuse column if already crated
            //  - column can already have some data used by different services (e.g. order)
            //  - it is a bit more efficient then to re-create column objects through sequential requests
            if (!data.column) {
                data.column = zemGridObject.createColumn(data);
            }
            return data.column;
        }

        return {
            clear: clear,
            parse: parse,
            parseMetaData: parseMetaData,
        };
    });
