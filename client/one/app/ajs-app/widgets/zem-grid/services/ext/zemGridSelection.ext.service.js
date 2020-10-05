angular
    .module('one.widgets')
    .factory('zemGridSelectionService', function(zemGridConstants) {
        // eslint-disable-line max-len

        //
        // Service providing selection functionality used by checkbox directives (header and cell)
        //

        function SelectionService(grid) {
            var pubsub = grid.meta.pubsub;

            initialize();

            //
            // Public API
            //
            this.destroy = destroy;
            this.getConfig = getConfig;
            this.setConfig = setConfig;
            this.getSelection = getSelection;
            this.clearSelection = clearSelection;
            this.setSelection = setSelection;
            this.setFilter = setFilter;
            this.getCustomFilters = getCustomFilters;
            this.getRowTooltip = getRowTooltip;

            this.isSelectionEnabled = isSelectionEnabled;
            this.isFilterSelectionEnabled = isFilterSelectionEnabled;
            this.isRowSelectionEnabled = isRowSelectionEnabled;
            this.isRowSelectable = isRowSelectable;
            this.isSelectionEmpty = isSelectionEmpty;

            this.isRowSelected = isRowSelected;
            this.setRowSelection = setRowSelection;

            var onDataUpdatedHandler;

            function initialize() {
                var restoreNeeded = false;
                onDataUpdatedHandler = pubsub.register(
                    pubsub.EVENTS.DATA_UPDATED,
                    null,
                    function() {
                        if (grid.body.rows.length === 0) {
                            restoreNeeded = true; // Full update in progress
                        } else if (restoreNeeded) {
                            // Restore selection with updated rows
                            grid.ext.selection.selected = restoreSelectionCollection(
                                grid.ext.selection.selected
                            );
                            grid.ext.selection.unselected = restoreSelectionCollection(
                                grid.ext.selection.unselected
                            );
                            pubsub.notify(
                                pubsub.EVENTS.EXT_SELECTION_UPDATED,
                                grid.ext.selection
                            );
                        }
                    }
                );

                grid.ext.selection = {};
                setFilter(zemGridConstants.gridSelectionFilterType.NONE);
            }

            function destroy() {
                if (onDataUpdatedHandler) onDataUpdatedHandler();
            }

            function restoreSelectionCollection(oldSelectionCollection) {
                var selectionCollection = [];
                oldSelectionCollection.forEach(function(oldRow) {
                    grid.body.rows.forEach(function(newRow) {
                        if (oldRow.id === newRow.id) {
                            selectionCollection.push(newRow);
                        }
                    });
                    if (grid.footer.row && grid.footer.row.id === oldRow.id) {
                        selectionCollection.push(grid.footer.row);
                    }
                });
                return selectionCollection;
            }

            function getSelection() {
                return grid.ext.selection;
            }

            function clearSelection() {
                setFilter(zemGridConstants.gridSelectionFilterType.NONE);
            }

            function setSelection(selection) {
                grid.ext.selection = selection;
                pubsub.notify(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    grid.ext.selection
                );
            }

            function setFilter(type, customFilter) {
                var filter = customFilter;
                if (type !== zemGridConstants.gridSelectionFilterType.CUSTOM) {
                    filter = {
                        callback: function() {
                            return (
                                type ===
                                zemGridConstants.gridSelectionFilterType.ALL
                            );
                        },
                    };
                }
                grid.ext.selection.type = type;
                grid.ext.selection.filter = filter;
                grid.ext.selection.selected = [];
                grid.ext.selection.unselected = [];
                pubsub.notify(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    grid.ext.selection
                );
            }

            function getConfig() {
                return grid.meta.options.selection;
            }

            function setConfig(config) {
                grid.meta.options.selection = config;
                pubsub.notify(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    getSelection()
                );
            }

            function getCustomFilters() {
                return getConfig().customFilters;
            }

            function isSelectionEnabled() {
                return getConfig().enabled;
            }

            function isFilterSelectionEnabled() {
                return getConfig().filtersEnabled;
            }

            function isRowSelectionEnabled(row) {
                if (row.type === zemGridConstants.gridRowType.GROUP) {
                    return getConfig().groupsEnabled;
                }
                return getConfig().levels.indexOf(row.level) >= 0;
            }

            function isRowSelectable(row) {
                if (!isRowSelectionEnabled(row)) return false;

                if (isRowSelected(row)) {
                    // Prevent un-selection of footer row if it's the only row selected
                    if (
                        row.level === zemGridConstants.gridRowLevel.FOOTER &&
                        isSelectionEmpty()
                    ) {
                        return false;
                    }
                    return true;
                }

                var config = getConfig();
                if (config.callbacks && config.callbacks.isRowSelectable) {
                    return config.callbacks.isRowSelectable(row);
                }
                return true;
            }

            function isRowSelected(row) {
                var isFiltered = getSelection().filter.callback(row);
                if (isFiltered) {
                    return getSelection().unselected.indexOf(row) < 0;
                }
                return getSelection().selected.indexOf(row) >= 0;
            }

            function setRowSelection(row, selected) {
                if (isRowSelected(row) === selected) return;

                var isFiltered = getSelection().filter.callback(row);
                // If item is filtered its selection would be persisted in unselected collection
                // since it will actually be unselected by user. If not filtered selected collection
                // is used.
                var collection = isFiltered
                    ? getSelection().unselected
                    : getSelection().selected;
                var idx = collection.indexOf(row);
                if (idx >= 0) {
                    collection.splice(idx, 1);
                } else {
                    collection.push(row);
                }
                pubsub.notify(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    getSelection()
                );
            }

            function getRowTooltip(row) {
                var config = getConfig();
                if (!config.info) return null;
                if (isRowSelectionEnabled(row) && !isRowSelectable(row))
                    return config.info.disabledRow;
                // TODO: extend functionality for other row states
                return null;
            }

            function isSelectionEmpty() {
                if (
                    getSelection().type !==
                    zemGridConstants.gridSelectionFilterType.NONE
                )
                    return false;

                var selectedRowsWithoutFooter = getSelection().selected.filter(
                    function(row) {
                        return (
                            row.level !== zemGridConstants.gridRowLevel.FOOTER
                        );
                    }
                );
                return selectedRowsWithoutFooter.length === 0;
            }
        }

        return {
            createInstance: function(grid) {
                return new SelectionService(grid);
            },
        };
    });
