/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridCollapseService', ['zemGridConstants', function (zemGridConstants) { // eslint-disable-line max-len

    function CollapseService (grid) {
        var pubsub = grid.meta.pubsub;

        initialize();

        //
        // Public API
        //
        this.isRowCollapsable = isRowCollapsable;
        this.isRowCollapsed = isRowCollapsed;
        this.setLevelCollapsed = setLevelCollapsed;
        this.setRowCollapsed = setRowCollapsed;

        function initialize () {
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, null, function () {
                pubsub.notify(pubsub.EVENTS.EXT_COLLAPSE_UPDATED);
            });
        }

        function isRowCollapsable (row) {
            if (row.level === zemGridConstants.gridRowLevel.FOOTER) return false;
            return grid.meta.dataService.getBreakdownLevel() > row.level;
        }

        function isRowCollapsed (row) {
            return row.collapsed;
        }

        function setLevelCollapsed (level, collapsed) {
            grid.body.rows.forEach(function (row) {
                if (row.level === level) {
                    row.collapsed = collapsed;
                    updateChildRows(row);
                }
            });
            pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        }

        function setRowCollapsed (row, collapsed) {
            row.collapsed = collapsed;
            updateChildRows(row);
            pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        }

        function updateChildRows (parent) {
            var idx = grid.body.rows.indexOf(parent);
            while (++idx < grid.body.rows.length) {
                var child = grid.body.rows[idx];
                if (child.level <= parent.level) break;
                child.visible = !parent.collapsed && !child.parent.collapsed;
            }
        }
    }

    return {
        createInstance: function (grid) {
            return new CollapseService(grid);
        }
    };
}]);
