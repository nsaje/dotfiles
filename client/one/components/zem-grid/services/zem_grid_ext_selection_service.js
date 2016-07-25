/* globals oneApp */
'use strict';

oneApp.factory('zemGridSelectionService', ['zemGridConstants', function (zemGridConstants) { // eslint-disable-line max-len

    //
    // Service providing selection functionality used by checkbox directives (header and cell)
    //

    function SelectionService (grid) {
        var pubsub = grid.meta.pubsub;

        initialize();

        //
        // Public API
        //
        this.getConfig = getConfig;
        this.setConfig = setConfig;
        this.getSelection = getSelection;
        this.setFilter = setFilter;
        this.getCustomFilters = getCustomFilters;

        this.isSelectionEnabled = isSelectionEnabled;
        this.isFilterSelectionEnabled = isFilterSelectionEnabled;
        this.isRowSelectionEnabled = isRowSelectionEnabled;
        this.isRowSelectable = isRowSelectable;

        this.isRowSelected = isRowSelected;
        this.setRowSelection = setRowSelection;

        function initialize () {
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, function () {
                if (grid.body.rows.length === 0) {
                    grid.ext.selection.selected = [];
                    grid.ext.selection.unselected = [];
                    pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, grid.ext.selection);
                }
            });

            grid.ext.selection = {};
            setFilter(zemGridConstants.gridSelectionFilterType.NONE);
        }

        function getSelection () {
            return grid.ext.selection;
        }

        function setSelection (selection) {
            grid.ext.selection = selection;
            pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, grid.ext.selection);
        }

        function setFilter (type, customFilter) {
            var filter = customFilter;
            if (type !== zemGridConstants.gridSelectionFilterType.CUSTOM) {
                filter = {
                    callback: function () {
                        return type === zemGridConstants.gridSelectionFilterType.ALL;
                    }
                };
            }
            grid.ext.selection.type = type;
            grid.ext.selection.filter = filter;
            grid.ext.selection.selected = [];
            grid.ext.selection.unselected = [];
            pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, grid.ext.selection);
        }

        function getConfig () {
            return grid.meta.options.selection;
        }

        function setConfig (config) {
            grid.meta.options.selection = config;
            pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, getSelection());
        }

        function getCustomFilters () {
            return getConfig().customFilters;
        }

        function isSelectionEnabled () {
            return getConfig().enabled;
        }

        function isFilterSelectionEnabled () {
            return getConfig().filtersEnabled;
        }

        function isRowSelectionEnabled (row) {
            return getConfig().levels.indexOf(row.level) >= 0;
        }

        function isRowSelectable (row) {
            var config = getConfig();
            var maxSelected = config.maxSelected;
            if (config.maxSelected && getSelection().selected.length >= maxSelected) {
                return !isRowSelected(row);
            }
            return false;
        }

        function isRowSelected (row) {
            var isFiltered = getSelection().filter.callback(row);
            if (isFiltered) {
                return getSelection().unselected.indexOf(row) < 0;
            }
            return getSelection().selected.indexOf(row) >= 0;
        }

        function setRowSelection (row, selected) {
            if (isRowSelected(row) === selected) return;

            var isFiltered = getSelection().filter.callback(row);
            // If item is filtered its selection would be persisted in unselected collection
            // since it will actually be unselected by user. If not filtered selected collection
            // is used.
            var collection = isFiltered ? getSelection().unselected : getSelection().selected;
            var idx = collection.indexOf(row);
            if (idx >= 0) {
                collection.splice(idx, 1);
            } else {
                collection.push(row);
            }
            pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, getSelection());
        }
    }


    return {
        createInstance: function (grid) {
            return new SelectionService(grid);
        }
    };
}]);
